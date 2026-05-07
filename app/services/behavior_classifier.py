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
    Rule-based classifier for horse behavior using keypoint coordinates
    
    Classifies the main 3 behaviors:
    - Standing
    - Walking
    - Eating/Drinking
    """
    
    def __init__(
        self,
        lying_height_ratio_threshold: float = 0.5,
        eating_height_ratio_threshold: float = 0.8,
        drinking_height_ratio_threshold: float = 0.6,
        movement_threshold: float = 10.0,
        likelihood_threshold: float = 0.6
    ):
        """
        Initialize the behavior classifier with configurable thresholds
        
        Args:
            lying_height_ratio_threshold: Y-position ratio for lying detection (0-1)
            eating_height_ratio_threshold: Y-position ratio for eating (0-1)
            drinking_height_ratio_threshold: Y-position ratio for drinking (0-1)
            movement_threshold: Pixel distance threshold for movement detection
            likelihood_threshold: Minimum confidence for keypoint validity
        """
        self.lying_height_ratio = lying_height_ratio_threshold
        self.eating_height_ratio = eating_height_ratio_threshold
        self.drinking_height_ratio = drinking_height_ratio_threshold
        self.movement_threshold = movement_threshold
        self.likelihood_threshold = likelihood_threshold
        
        # Behavior thresholds (extracted from magic numbers)
        self._REARING_HEIGHT_RATIO_DIFF = 0.15
        self._EATING_NECK_TOLERANCE = 0.15
        self._HEAD_SHAKE_HORIZ_MOV_PX = 15.0
        self._HEAD_SHAKE_NECK_MOV_PX = 10.0
        self._GROOMING_BELLY_DISTANCE_PX = 80.0
        self._GROOMING_KNEE_DISTANCE_PX = 100.0
        self._KICKING_UPWARD_MOVEMENT_PX = 25.0
        self._KICKING_BACKWARD_MOVEMENT_PX = 15.0
        self._TAIL_SWISH_MOVEMENT_PX = 12.0
        
        
        # Essential keypoints for classification
        self.essential_keypoints = [
            'back_middle',      # Withers/back reference
            'nose',             # Head position
            'front_left_paw',   # Front left hoof
            'front_right_paw',  # Front right hoof
            'back_left_paw',    # Back left hoof
            'back_right_paw'    # Back right hoof
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
        """
        Check if a keypoint exists and has sufficient likelihood
        
        Args:
            keypoints: Dictionary of keypoints {name: (x, y, likelihood)}
            keypoint_name: Name of the keypoint to validate
            
        Returns:
            True if keypoint is valid, False otherwise
        """
        if keypoint_name not in keypoints:
            return False
        
        x, y, likelihood = keypoints[keypoint_name]
        return likelihood >= self.likelihood_threshold
    
    def _get_keypoint_coords(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        keypoint_name: str
    ) -> Optional[Tuple[float, float]]:
        """
        Safely extract (x, y) coordinates from keypoint
        
        Args:
            keypoints: Dictionary of keypoints
            keypoint_name: Name of the keypoint
            
        Returns:
            (x, y) tuple or None if keypoint is invalid
        """
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
        """
        Calculate average movement between frames
        
        Args:
            current_keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            reference_points: List of keypoint names to track (default: hooves)
            
        Returns:
            Average Euclidean distance moved
        """
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
                # Calculate Euclidean distance
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
        """
        Check if horse is lying down based on body position
        
        Args:
            keypoints: Current frame keypoints
            frame_height: Height of the video frame
            
        Returns:
            True if horse appears to be lying down
        """
        # Use back_middle (withers) and hooves for lying detection
        back_coords = self._get_keypoint_coords(keypoints, 'back_middle')
        
        if back_coords is None:
            return False
        
        # Check if withers are low (remember: y increases downward)
        withers_y_ratio = back_coords[1] / frame_height
        
        # Also check if hooves are at similar height (body is horizontal)
        hoof_points = ['front_left_paw', 'front_right_paw', 'back_left_paw', 'back_right_paw']
        hoof_y_coords = []
        
        for hoof in hoof_points:
            coords = self._get_keypoint_coords(keypoints, hoof)
            if coords is not None:
                hoof_y_coords.append(coords[1])
        
        if hoof_y_coords:
            avg_hoof_y = np.mean(hoof_y_coords)
            hoof_y_ratio = avg_hoof_y / frame_height
            
            # If both body and hooves are low, likely lying down
            if withers_y_ratio > self.lying_height_ratio and hoof_y_ratio > self.lying_height_ratio:
                return True
        
        return False
    
    def _check_eating_or_drinking(
        self,
        keypoints: Dict[str, Tuple[float, float, float]],
        frame_height: int
    ) -> Optional[str]:
        """
        Check if horse is eating or drinking based on head position
        
        Improved logic to distinguish between:
        - Head lowered to eat (nose AND neck very low)
        - Head moderately lowered to drink (nose AND neck moderately low)
        - Head turned sideways while standing (nose low but neck still up)
        
        Args:
            keypoints: Current frame keypoints
            frame_height: Height of the video frame
            
        Returns:
            "Eating" or "Drinking" if detected, else None
        """
        nose_coords = self._get_keypoint_coords(keypoints, 'nose')
        neck_base_coords = self._get_keypoint_coords(keypoints, 'neck_base')
        
        if nose_coords is None:
            return None
        
        # Check if nose is low (near ground or feeder)
        nose_y_ratio = nose_coords[1] / frame_height
        
        # Additional check: if we have neck_base, verify the head is actually lowered
        # (not just turned sideways). When eating/drinking, BOTH nose and neck should be low.
        if neck_base_coords is not None:
            neck_y_ratio = neck_base_coords[1] / frame_height
            
            # For eating/drinking: nose must be low AND neck must be reasonably lowered too
            # Check for Eating first (lower threshold)
            eating_neck_threshold = self.eating_height_ratio - self._EATING_NECK_TOLERANCE
            drinking_neck_threshold = self.drinking_height_ratio - self._EATING_NECK_TOLERANCE
            
            if nose_y_ratio > self.eating_height_ratio:
                if neck_y_ratio > eating_neck_threshold:
                    return "Eating"
            # If not Eating, check for Drinking
            if nose_y_ratio > self.drinking_height_ratio:
                if neck_y_ratio > drinking_neck_threshold:
                    return "Drinking"
            # If nose is low but neck is high - likely looking sideways
            return None
        else:
            # If neck_base not available, fall back to nose-only detection
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
        """
        Check if horse is rearing (standing on hind legs)
        
        Args:
            keypoints: Current frame keypoints
            frame_height: Height of the video frame
            
        Returns:
            True if horse appears to be rearing
        """
        # Get front and back paw positions
        front_left = self._get_keypoint_coords(keypoints, 'front_left_paw')
        front_right = self._get_keypoint_coords(keypoints, 'front_right_paw')
        back_left = self._get_keypoint_coords(keypoints, 'back_left_paw')
        back_right = self._get_keypoint_coords(keypoints, 'back_right_paw')
        back_middle = self._get_keypoint_coords(keypoints, 'back_middle')
        
        if not all([front_left, front_right, back_left, back_right, back_middle]):
            return False
        
        # Calculate average y-position of front and back paws
        avg_front_y = (front_left[1] + front_right[1]) / 2
        avg_back_y = (back_left[1] + back_right[1]) / 2
        
        # Rearing: front paws significantly higher (smaller y) than back paws
        # and back_middle is high relative to back paws
        if avg_front_y < avg_back_y - (frame_height * self._REARING_HEIGHT_RATIO_DIFF):
            if back_middle[1] < avg_back_y:  # Body is elevated
                return True
        
        return False
    
    def _check_head_shaking(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        """
        Check if horse is shaking its head (horizontal movement)
        
        Args:
            current_keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            
        Returns:
            True if head is shaking horizontally
        """
        curr_nose = self._get_keypoint_coords(current_keypoints, 'nose')
        prev_nose = self._get_keypoint_coords(prev_keypoints, 'nose')
        curr_neck = self._get_keypoint_coords(current_keypoints, 'neck_end')
        prev_neck = self._get_keypoint_coords(prev_keypoints, 'neck_end')
        
        if not all([curr_nose, prev_nose, curr_neck, prev_neck]):
            return False
        
        # Calculate horizontal movement
        nose_horizontal_movement = abs(curr_nose[0] - prev_nose[0])
        nose_vertical_movement = abs(curr_nose[1] - prev_nose[1])
        
        neck_horizontal_movement = abs(curr_neck[0] - prev_neck[0])
        
        # Head shaking: significant horizontal movement with minimal vertical movement
        if nose_horizontal_movement > self._HEAD_SHAKE_HORIZ_MOV_PX and nose_horizontal_movement > nose_vertical_movement * 2:
            if neck_horizontal_movement > self._HEAD_SHAKE_NECK_MOV_PX:  # Neck also moving
                return True
        
        return False
    
    def _check_grooming(
        self,
        keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        """
        Check if horse is grooming/scratching itself
        
        Args:
            keypoints: Current frame keypoints
            
        Returns:
            True if horse appears to be grooming
        """
        nose = self._get_keypoint_coords(keypoints, 'nose')
        belly = self._get_keypoint_coords(keypoints, 'belly_bottom')
        back_left_knee = self._get_keypoint_coords(keypoints, 'back_left_knee')
        back_right_knee = self._get_keypoint_coords(keypoints, 'back_right_knee')
        
        if not nose:
            return False
        
        # Check if nose is near belly or back legs (grooming behavior)
        if belly:
            distance_to_belly = np.sqrt((nose[0] - belly[0])**2 + (nose[1] - belly[1])**2)
            if distance_to_belly < self._GROOMING_BELLY_DISTANCE_PX:  # Nose near belly
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
        """
        Check if horse is kicking (rapid backward movement of back legs)
        
        Args:
            current_keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            
        Returns:
            True if horse appears to be kicking
        """
        curr_back_left = self._get_keypoint_coords(current_keypoints, 'back_left_paw')
        prev_back_left = self._get_keypoint_coords(prev_keypoints, 'back_left_paw')
        curr_back_right = self._get_keypoint_coords(current_keypoints, 'back_right_paw')
        prev_back_right = self._get_keypoint_coords(prev_keypoints, 'back_right_paw')
        
        if not all([curr_back_left, prev_back_left, curr_back_right, prev_back_right]):
            return False
        
        # Calculate backward movement (assuming horse faces right, backward is negative x)
        left_movement_x = curr_back_left[0] - prev_back_left[0]
        right_movement_x = curr_back_right[0] - prev_back_right[0]
        
        # Also check upward movement (kicking lifts legs)
        left_movement_y = prev_back_left[1] - curr_back_left[1]  # Remember: y increases downward
        right_movement_y = prev_back_right[1] - curr_back_right[1]
        
        # Kicking: rapid upward and backward movement of back legs
        avg_upward = (left_movement_y + right_movement_y) / 2
        
        if avg_upward > self._KICKING_UPWARD_MOVEMENT_PX:  # Significant upward movement
            # Either or both legs moving rapidly
            if abs(left_movement_x) > self._KICKING_BACKWARD_MOVEMENT_PX or abs(right_movement_x) > self._KICKING_BACKWARD_MOVEMENT_PX:
                return True
        
        return False
    
    def _check_tail_swishing(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        """
        Check if horse is swishing its tail
        
        Args:
            current_keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            
        Returns:
            True if tail is swishing
        """
        curr_tail = self._get_keypoint_coords(current_keypoints, 'tail_base')
        prev_tail = self._get_keypoint_coords(prev_keypoints, 'tail_base')
        
        if not all([curr_tail, prev_tail]):
            return False
        
        # Calculate tail movement
        tail_movement = np.sqrt((curr_tail[0] - prev_tail[0])**2 + (curr_tail[1] - prev_tail[1])**2)
        
        # Tail swishing: noticeable movement of tail base
        if tail_movement > self._TAIL_SWISH_MOVEMENT_PX:
            return True
        
        return False
    
    def _check_turning(
        self,
        current_keypoints: Dict[str, Tuple[float, float, float]],
        prev_keypoints: Dict[str, Tuple[float, float, float]]
    ) -> bool:
        """
        Check if horse is turning (rotation behavior)
        
        Args:
            current_keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            
        Returns:
            True if horse is turning
        """
        # Get nose (front) and tail_base (back) positions
        curr_nose = self._get_keypoint_coords(current_keypoints, 'nose')
        prev_nose = self._get_keypoint_coords(prev_keypoints, 'nose')
        curr_tail = self._get_keypoint_coords(current_keypoints, 'tail_base')
        prev_tail = self._get_keypoint_coords(prev_keypoints, 'tail_base')
        
        if not all([curr_nose, prev_nose, curr_tail, prev_tail]):
            return False
        
        # Calculate movement direction of front vs back
        nose_dx = curr_nose[0] - prev_nose[0]
        tail_dx = curr_tail[0] - prev_tail[0]
        
        # Turning: front and back moving in opposite horizontal directions
        if nose_dx * tail_dx < -25:  # Opposite signs and significant movement
            return True
        
        return False
    
    def _classify_movement_type(
        self,
        movement_magnitude: float
    ) -> str:
        """
        Classify type of movement based on magnitude
        
        Args:
            movement_magnitude: Average movement distance in pixels
            
        Returns:
            Movement type: "Walking", "Running", or "Moving"
        """
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
        """
        Classify horse behavior based on keypoint positions
        
        Args:
            current_keypoints: Dictionary of keypoints {name: (x, y, likelihood)}
            prev_keypoints: Optional dictionary of previous frame keypoints
            frame_height: Height of the video frame in pixels
            
        Returns:
            Behavior classification string (e.g., "Standing", "Walking")
        """
        # Validate essential keypoints
        valid_keypoints = sum(
            1 for kp in self.essential_keypoints
            if self._validate_keypoint(current_keypoints, kp)
        )
        
        if valid_keypoints < len(self.essential_keypoints) // 2:
            logger.warning("Insufficient valid keypoints for classification")
            return "Unknown"
        
        # We simplify to only 3 main behaviors: Walking (Moving), Eating/Drinking, and Standing.
        
        # 1. Check for Movement (Walking)
        if prev_keypoints is not None:
            movement_magnitude = self._calculate_movement_magnitude(
                current_keypoints, prev_keypoints
            )
            if movement_magnitude > self.movement_threshold:
                return "Walking"
        
        # 2. Check for Eating/Drinking
        # For simplicity, if it's eating or drinking, we'll return "Eating/Drinking"
        
        # Check coordinates and ratios manually for the simple 3-class logic
        nose_coords = self._get_keypoint_coords(current_keypoints, 'nose')
        back_coords = self._get_keypoint_coords(current_keypoints, 'back_middle')
        if nose_coords and back_coords:
            nose_y = nose_coords[1]
            back_y = back_coords[1]
            
            # If nose is low relative to the frame/back, it's eating/drinking
            if nose_y > (frame_height * 0.6) and nose_y > back_y:
                return "Eating/Drinking"

        # 3. Default to Standing
        return "Standing"
    
    def get_behavior_confidence(
        self,
        keypoints: Dict[str, Tuple[float, float, float]]
    ) -> float:
        """
        Calculate confidence score based on keypoint likelihood
        
        Args:
            keypoints: Dictionary of keypoints
            
        Returns:
            Average likelihood of essential keypoints (0-1)
        """
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
    """
    Convenience function for quick behavior classification
    
    Args:
        current_keypoints: Dictionary of keypoints {name: (x, y, likelihood)}
        prev_keypoints: Optional dictionary of previous frame keypoints
        frame_height: Height of the video frame in pixels
        
    Returns:
        Behavior classification string
    
    Example:
        >>> keypoints = {
        ...     'nose': (320, 400, 0.95),
        ...     'back_middle': (300, 200, 0.92),
        ...     'front_left_paw': (250, 450, 0.88)
        ... }
        >>> behavior = classify_horse_behavior(keypoints, frame_height=480)
        >>> print(behavior)  # "Eating"
    """
    classifier = HorseBehaviorClassifier()
    return classifier.classify_behavior(current_keypoints, prev_keypoints, frame_height)
