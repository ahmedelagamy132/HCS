"""
Horse Behavior Classification Service
Classifies horse behavior based on DeepLabCut keypoint coordinates
"""
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class HorseBehaviorClassifier:
    """
    Rule-based classifier for horse behavior using keypoint coordinates.

    Classifies: Standing, Eating, Drinking, Walking, Running/Trotting, Rearing,
    Head Shaking, Grooming/Scratching, Turning, Kicking, Tail Swishing
    """

    def __init__(
        self,
        lying_height_ratio_threshold: float = 0.5,
        eating_height_ratio_threshold: float = 0.8,
        drinking_height_ratio_threshold: float = 0.6,
        movement_threshold: float = 10.0,
        likelihood_threshold: float = 0.6
    ):
        self.lying_height_ratio = lying_height_ratio_threshold
        self.eating_height_ratio = eating_height_ratio_threshold
        self.drinking_height_ratio = drinking_height_ratio_threshold
        self.movement_threshold = movement_threshold
        self.likelihood_threshold = likelihood_threshold

        self._REARING_HEIGHT_RATIO_DIFF = 0.15
        self._EATING_NECK_TOLERANCE = 0.15
        self._HEAD_SHAKE_HORIZ_MOV_PX = 15.0
        self._HEAD_SHAKE_NECK_MOV_PX = 10.0
        self._GROOMING_BELLY_DISTANCE_PX = 80.0
        self._GROOMING_KNEE_DISTANCE_PX = 100.0
        self._KICKING_UPWARD_MOVEMENT_PX = 25.0
        self._KICKING_BACKWARD_MOVEMENT_PX = 15.0
        self._TAIL_SWISH_MOVEMENT_PX = 12.0

        self.essential_keypoints = [
            'back_middle',
            'nose',
            'front_left_paw',
            'front_right_paw',
            'back_left_paw',
            'back_right_paw'
        ]

        logger.info(f"HorseBehaviorClassifier initialized with thresholds: "
                   f"lying={lying_height_ratio_threshold}, "
                   f"eating={eating_height_ratio_threshold}, "
                   f"drinking={drinking_height_ratio_threshold}, "
                   f"movement={movement_threshold}")

    def _validate_keypoint(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        keypoint_name: str
    ) -> bool:
        if keypoint_name not in keypoints:
            return False
        x, y, likelihood = keypoints[keypoint_name]
        return likelihood >= self.likelihood_threshold

    def _get_keypoint_coords(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        keypoint_name: str
    ) -> Optional[Tuple[float, float]]:
        if not self._validate_keypoint(keypoints, keypoint_name):
            return None
        x, y, likelihood = keypoints[keypoint_name]
        return (x, y)

    def _calculate_movement_magnitude(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]],
        reference_points: list = None
    ) -> float:
        if reference_points is None:
            reference_points = [
                'front_left_paw', 'front_right_paw',
                'back_left_paw', 'back_right_paw'
            ]

        distances = []

        for keypoint_name in reference_points:
            curr_coords = self._get_keypoint_coords(current_keypoints, keypoint_name)
            prev_coords = self._get_keypoint_coords(prev_keypoints, keypoint_name)

            if curr_coords is not None and prev_coords is not None:
                distance = np.sqrt(
                    (curr_coords[0] - prev_coords[0])**2 +
                    (curr_coords[1] - prev_coords[1])**2
                )
                distances.append(distance)

        if not distances:
            return 0.0

        return np.mean(distances)

    def _check_lying_down(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        frame_height: int
    ) -> bool:
        back_coords = self._get_keypoint_coords(keypoints, 'back_middle')

        if back_coords is None:
            return False

        withers_y_ratio = back_coords[1] / frame_height

        hoof_points = ['front_left_paw', 'front_right_paw', 'back_left_paw', 'back_right_paw']
        hoof_y_coords = []

        for hoof in hoof_points:
            coords = self._get_keypoint_coords(keypoints, hoof)
            if coords is not None:
                hoof_y_coords.append(coords[1])

        if hoof_y_coords:
            avg_hoof_y = np.mean(hoof_y_coords)
            hoof_y_ratio = avg_hoof_y / frame_height

            if withers_y_ratio > self.lying_height_ratio and hoof_y_ratio > self.lying_height_ratio:
                return True

        return False

    def _check_eating_or_drinking(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        frame_height: int
    ) -> Optional[str]:
        nose_coords = self._get_keypoint_coords(keypoints, 'nose')
        neck_base_coords = self._get_keypoint_coords(keypoints, 'neck_base')

        if nose_coords is None:
            return None

        nose_y_ratio = nose_coords[1] / frame_height

        if neck_base_coords is not None:
            neck_y_ratio = neck_base_coords[1] / frame_height

            eating_neck_threshold = self.eating_height_ratio - self._EATING_NECK_TOLERANCE
            drinking_neck_threshold = self.drinking_height_ratio - self._EATING_NECK_TOLERANCE

            if nose_y_ratio > self.eating_height_ratio:
                if neck_y_ratio > eating_neck_threshold:
                    return "Eating"
            if nose_y_ratio > self.drinking_height_ratio:
                if neck_y_ratio > drinking_neck_threshold:
                    return "Drinking"
            return None
        else:
            if nose_y_ratio > self.eating_height_ratio:
                return "Eating"
            elif nose_y_ratio > self.drinking_height_ratio:
                return "Drinking"

        return None

    def _check_rearing(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        frame_height: int
    ) -> bool:
        front_left = self._get_keypoint_coords(keypoints, 'front_left_paw')
        front_right = self._get_keypoint_coords(keypoints, 'front_right_paw')
        back_left = self._get_keypoint_coords(keypoints, 'back_left_paw')
        back_right = self._get_keypoint_coords(keypoints, 'back_right_paw')
        back_middle = self._get_keypoint_coords(keypoints, 'back_middle')

        if not all([front_left, front_right, back_left, back_right, back_middle]):
            return False

        avg_front_y = (front_left[1] + front_right[1]) / 2
        avg_back_y = (back_left[1] + back_right[1]) / 2

        if avg_front_y < avg_back_y - (frame_height * self._REARING_HEIGHT_RATIO_DIFF):
            if back_middle[1] < avg_back_y:
                return True

        return False

    def _check_head_shaking(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        curr_nose = self._get_keypoint_coords(current_keypoints, 'nose')
        prev_nose = self._get_keypoint_coords(prev_keypoints, 'nose')
        curr_neck = self._get_keypoint_coords(current_keypoints, 'neck_end')
        prev_neck = self._get_keypoint_coords(prev_keypoints, 'neck_end')

        if not all([curr_nose, prev_nose, curr_neck, prev_neck]):
            return False

        nose_horizontal_movement = abs(curr_nose[0] - prev_nose[0])
        nose_vertical_movement = abs(curr_nose[1] - prev_nose[1])
        neck_horizontal_movement = abs(curr_neck[0] - prev_neck[0])

        if nose_horizontal_movement > self._HEAD_SHAKE_HORIZ_MOV_PX and nose_horizontal_movement > nose_vertical_movement * 2:
            if neck_horizontal_movement > self._HEAD_SHAKE_NECK_MOV_PX:
                return True

        return False

    def _check_grooming(
        self,
        keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        nose = self._get_keypoint_coords(keypoints, 'nose')
        belly = self._get_keypoint_coords(keypoints, 'belly_bottom')
        back_left_knee = self._get_keypoint_coords(keypoints, 'back_left_knee')
        back_right_knee = self._get_keypoint_coords(keypoints, 'back_right_knee')

        if not nose:
            return False

        if belly:
            distance_to_belly = np.sqrt((nose[0] - belly[0])**2 + (nose[1] - belly[1])**2)
            if distance_to_belly < self._GROOMING_BELLY_DISTANCE_PX:
                return True

        if back_left_knee:
            distance_to_back_left = np.sqrt((nose[0] - back_left_knee[0])**2 + (nose[1] - back_left_knee[1])**2)
            if distance_to_back_left < self._GROOMING_KNEE_DISTANCE_PX:
                return True

        if back_right_knee:
            distance_to_back_right = np.sqrt((nose[0] - back_right_knee[0])**2 + (nose[1] - back_right_knee[1])**2)
            if distance_to_back_right < self._GROOMING_KNEE_DISTANCE_PX:
                return True

        return False

    def _check_kicking(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        curr_back_left = self._get_keypoint_coords(current_keypoints, 'back_left_paw')
        prev_back_left = self._get_keypoint_coords(prev_keypoints, 'back_left_paw')
        curr_back_right = self._get_keypoint_coords(current_keypoints, 'back_right_paw')
        prev_back_right = self._get_keypoint_coords(prev_keypoints, 'back_right_paw')

        if not all([curr_back_left, prev_back_left, curr_back_right, prev_back_right]):
            return False

        left_movement_x = curr_back_left[0] - prev_back_left[0]
        right_movement_x = curr_back_right[0] - prev_back_right[0]

        left_movement_y = prev_back_left[1] - curr_back_left[1]
        right_movement_y = prev_back_right[1] - curr_back_right[1]

        avg_upward = (left_movement_y + right_movement_y) / 2

        if avg_upward > self._KICKING_UPWARD_MOVEMENT_PX:
            if abs(left_movement_x) > self._KICKING_BACKWARD_MOVEMENT_PX or abs(right_movement_x) > self._KICKING_BACKWARD_MOVEMENT_PX:
                return True

        return False

    def _check_tail_swishing(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        curr_tail = self._get_keypoint_coords(current_keypoints, 'tail_base')
        prev_tail = self._get_keypoint_coords(prev_keypoints, 'tail_base')

        if not all([curr_tail, prev_tail]):
            return False

        tail_movement = np.sqrt((curr_tail[0] - prev_tail[0])**2 + (curr_tail[1] - prev_tail[1])**2)

        if tail_movement > self._TAIL_SWISH_MOVEMENT_PX:
            return True

        return False

    def _check_turning(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        curr_nose = self._get_keypoint_coords(current_keypoints, 'nose')
        prev_nose = self._get_keypoint_coords(prev_keypoints, 'nose')
        curr_tail = self._get_keypoint_coords(current_keypoints, 'tail_base')
        prev_tail = self._get_keypoint_coords(prev_keypoints, 'tail_base')

        if not all([curr_nose, prev_nose, curr_tail, prev_tail]):
            return False

        nose_dx = curr_nose[0] - prev_nose[0]
        tail_dx = curr_tail[0] - prev_tail[0]

        if nose_dx * tail_dx < -25:
            return True

        return False

    def _classify_movement_type(self, movement_magnitude: float) -> str:
        if movement_magnitude > 30:
            return "Running/Trotting"
        elif movement_magnitude > self.movement_threshold:
            return "Walking"
        else:
            return "Moving"

    def classify_behavior(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Optional[Dict[str, Tuple[float, float, float]]] = None,
        frame_height: int = 480
    ) -> str:
        valid_keypoints = sum(
            1 for kp in self.essential_keypoints
            if self._validate_keypoint(current_keypoints, kp)
        )

        if valid_keypoints < len(self.essential_keypoints) // 2:
            logger.warning("Insufficient valid keypoints for classification")
            return "Unknown"

        if self._check_lying_down(current_keypoints, frame_height):
            return "Lying Down"

        if self._check_rearing(current_keypoints, frame_height):
            return "Rearing"

        if prev_keypoints is not None:
            if self._check_kicking(current_keypoints, prev_keypoints):
                return "Kicking"

            if self._check_head_shaking(current_keypoints, prev_keypoints):
                return "Head Shaking"

            if self._check_tail_swishing(current_keypoints, prev_keypoints):
                return "Tail Swishing"

            if self._check_turning(current_keypoints, prev_keypoints):
                return "Turning"

            movement_magnitude = self._calculate_movement_magnitude(
                current_keypoints, prev_keypoints
            )

            if movement_magnitude > self.movement_threshold:
                return self._classify_movement_type(movement_magnitude)

        if self._check_grooming(current_keypoints):
            return "Grooming/Scratching"

        eating_drinking_status = self._check_eating_or_drinking(current_keypoints, frame_height)
        if eating_drinking_status:
            return eating_drinking_status

        return "Standing"

    def get_behavior_confidence(
        self,
        keypoints: Dict[str, Tuple[float, float, float]]
    ) -> float:
        likelihoods = []

        for keypoint_name in self.essential_keypoints:
            if keypoint_name in keypoints:
                x, y, likelihood = keypoints[keypoint_name]
                likelihoods.append(likelihood)

        if not likelihoods:
            return 0.0

        return np.mean(likelihoods)


def classify_horse_behavior(
    current_keypoints: Dict[str, Tuple[float, float, float]],
    prev_keypoints: Optional[Dict[str, Tuple[float, float, float]]] = None,
    frame_height: int = 480
) -> str:
    classifier = HorseBehaviorClassifier()
    return classifier.classify_behavior(current_keypoints, prev_keypoints, frame_height)
