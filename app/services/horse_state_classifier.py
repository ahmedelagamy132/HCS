"""
Horse State Classifier - Object-Oriented Version

A class-based horse behavior classification system using Ollama vision models.
"""

import time
import os
import glob
import shutil
from typing import Dict, List, Optional, Union

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import ollama
except ImportError:
    raise ImportError("Please install: pip install ollama")


class HorseStateClassifier:
    """
    Horse behavior state classifier using Ollama vision models.
    """

    ALLOWED_STATES = ["standing", "walking", "running", "lying", "eating", "sitting"]

    STATE_SYNONYMS = {
        "stand": "standing",
        "still": "standing",
        "idle": "standing",
        "walk": "walking",
        "run": "running",
        "lying down": "lying",
        "laying": "lying",
        "lay": "lying",
        "resting": "lying",
        "graze": "eating",
        "grazing": "eating",
        "feed": "eating",
        "feeding": "eating",
        "eat": "eating",
        "sit": "sitting",
    }

    def __init__(
        self,
        model: str = "qwen2.5vl:7b",
        enable_visualization: bool = False,
        enable_metrics: bool = True,
        keep_alive_duration: str = "30m"
    ):
        self.model = model
        self.enable_visualization = enable_visualization
        self.enable_metrics = enable_metrics
        self.keep_alive_duration = keep_alive_duration

        self._is_warmed_up = False
        self._prediction_count = 0
        self._total_inference_time = 0

        if self.enable_visualization and not HAS_CV2:
            print("Warning: OpenCV not available. Visualization disabled.")
            self.enable_visualization = False

        if self.enable_metrics:
            print(f"HorseStateClassifier initialized")
            print(f"  Model: {self.model}")
            print(f"  Keep-alive: {self.keep_alive_duration}\n")
        self.prompt = self._create_prompt(self.model)

    def _normalize_state(self, text: str) -> str:
        t = (text or "").strip().lower().replace(".", "").replace(",", "").replace('"', "").replace("'", "")

        if t in self.ALLOWED_STATES:
            return t

        if t in self.STATE_SYNONYMS:
            return self.STATE_SYNONYMS[t]

        for k, v in self.STATE_SYNONYMS.items():
            if k in t:
                return v

        for s in self.ALLOWED_STATES:
            if s in t:
                return s

        return "standing"

    def _create_prompt(self, model_name: str) -> str:
        states_comma = ", ".join(self.ALLOWED_STATES)
        states_bullet = "\n".join([f"- {state}" for state in self.ALLOWED_STATES])

        prompts = {
            "gemma3:4b": f"""<start_of_turn>user
        Classify this horse's activity with ONE word.

        **ANALYZE IN THIS EXACT ORDER:**

        1. **MOTION CHECK**: Is the horse moving?
        - FAST motion (multiple legs airborne, mane flowing, dynamic pose)? → **running**
        - SLOW motion (one leg lifted, forward movement)? → **walking**

        2. **POSTURE CHECK**: Is the horse's BODY (torso/barrel) on the ground?
        - YES (lying flat, belly down)? → **lying**

        3. **FEEDING CHECK**: Is the head actively at a food source?
        - Muzzle IN grass/bucket/hay AND eating? → **eating**
        - Head just lowered but no food visible? → **standing**

        4. **DEFAULT**: If none above → **standing**

        Valid responses: {states_comma}

        Classify:<end_of_turn>
        <start_of_turn>model
        """,

            "llava-phi3": f"""You are an expert equine behavior analyst with computer vision capabilities.
            *   **Absolutely no extra text, no explanations, no greetings, no punctuation.**
        Your task is to analyze the provided image and classify the horse's primary activity.

        You MUST choose exactly one word from this list:
        {states_bullet}

        Definitions:
        * 'standing': Stationary on all four legs, not otherwise engaged.
        * 'walking': Moving slowly with a regular gait.
        * 'running': Moving fast (galloping, cantering).
        * 'lying': On the ground, either resting or fully recumbent.
        * 'eating': Actively consuming food (grazing, hay, etc.). Head is near food.
        * 'sitting': In a sitting position (rare).

        Rules:
        1. 'eating' always takes priority over 'standing'.
        2. If multiple horses are visible, classify the most central or prominent one.
        3. If highly ambiguous, default to 'standing'.

        Your output MUST be ONLY the single, lowercase classification word.

        Classification:""",

            "qwen2.5vl:7b": f"""You are an expert equine behavior analyst with computer vision capabilities.
Your task is to analyze the provided image and classify the horse's primary activity.
  First, identify the one activity that best describes the horse.
    You MUST choose exactly one word from this list:

    {states_bullet}
    Definitions:
    * 'standing': Stationary on all four legs, not otherwise engaged.
    * 'walking': Moving slowly with a regular gait.
    * 'running': Moving fast (galloping, cantering).
    * 'lying': On the ground, either resting or fully recumbent.
    * 'eating': Actively consuming food (grazing, hay, etc.). Head is near food.
    * 'sitting': In a sitting position (rare).

    Rules:
    1. 'eating' always takes priority over 'standing'.
    2. If multiple horses are visible, classify the most central or prominent one.
    3. If highly ambiguous, default to 'standing'.

    Your output MUST be ONLY the single, lowercase classification word.

    Classification:""",

            "qwen3:8b": f"""You are an expert equine behavior analyst with computer vision capabilities.
Your task is to analyze the provided image and classify the horse's primary activity.

Choose EXACTLY ONE word from this list:
{states_bullet}

Definitions:
- standing: Stationary on all four legs, not performing any other activity
- walking: Moving slowly with a regular gait
- running: Moving fast, galloping or cantering
- lying: On the ground, resting or fully recumbent
- eating: Actively consuming food — head near grass, hay, or bucket
- sitting: In a sitting position (rare)

Rules:
1. If the horse is eating while standing, choose 'eating' (eating takes priority)
2. Motion always overrides eating
3. Body flat on ground always means 'lying'
4. If uncertain, default to 'standing'
5. If multiple horses are visible, classify the most central/prominent one

Respond with ONLY ONE lowercase word. No punctuation, no explanation.

Classification:""",

            "default": f"""You are an expert equine behavior analyst with computer vision capabilities.

TASK: Analyze this image and classify the horse's current state/activity.

ALLOWED STATES (choose EXACTLY one):
{states_bullet}

CLASSIFICATION RULES:
1. 'standing': Horse is stationary on all four legs, not performing any other activity
2. 'walking': Horse is moving slowly with a regular gait, at least one hoof off ground
3. 'running': Horse is moving fast, galloping or cantering, multiple hooves off ground
4. 'lying': Horse is on the ground, lying down or resting (sitting or fully recumbent)
5. 'eating': Horse is actively consuming food (grazing, eating hay, or feed) - head down near food
6. 'sitting': Horse is in a sitting position (rare, but distinct from lying)

IMPORTANT INSTRUCTIONS:
- Respond with ONLY ONE WORD from the allowed states list
- Use lowercase only
- No punctuation, quotation marks, or explanation
- If the activity is ambiguous, choose the most prominent/dominant behavior
- If eating while standing, choose 'eating' (eating takes priority)
- If multiple horses, focus on the most prominent/centered horse
- If uncertain, default to 'standing'

Your response (one word only):"""
        }

        return prompts.get(model_name, prompts["default"])

    def _resize_image(self, image_path: str, size: Union[int, tuple], output_dir: Optional[str] = None) -> str:
        if not HAS_PIL:
            raise ImportError("PIL/Pillow is required for image resizing. Install with: pip install Pillow")

        img = Image.open(image_path)
        original_width, original_height = img.size

        if isinstance(size, int):
            target_size = (size, size)
            size_str = f"{size}x{size}"
        elif isinstance(size, tuple) and len(size) == 2:
            target_size = size
            size_str = f"{size[0]}x{size[1]}"
        else:
            raise ValueError(f"Invalid size parameter: {size}. Expected int or tuple of (width, height)")

        if target_size[0] >= original_width and target_size[1] >= original_height:
            return image_path

        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        img_resized = img.resize(target_size, Image.Resampling.LANCZOS)

        if output_dir is None:
            parent_dir = os.path.dirname(image_path)
            output_dir = os.path.join(parent_dir, "temp_images")

        os.makedirs(output_dir, exist_ok=True)

        base_name = os.path.basename(image_path)
        name, _ = os.path.splitext(base_name)
        resized_path = os.path.join(output_dir, f"{name}_resized_{size_str}.jpg")

        img_resized.save(resized_path, 'JPEG', quality=95)

        return resized_path

    def warm_up(self, dummy_image_path: Optional[str] = None) -> Dict:
        if self._is_warmed_up:
            return {'already_warm': True, 'model': self.model}

        if self.enable_metrics:
            print(f"Warming up model '{self.model}'...")

        start = time.time()

        try:
            if dummy_image_path and os.path.exists(dummy_image_path):
                response = ollama.chat(
                    model=self.model,
                    messages=[{
                        'role': 'user',
                        'content': 'Describe this image in one word.',
                        'images': [os.path.abspath(dummy_image_path)]
                    }],
                    options={'num_predict': 10},
                    keep_alive=self.keep_alive_duration
                )
            else:
                response = ollama.chat(
                    model=self.model,
                    messages=[{'role': 'user', 'content': 'Hi'}],
                    options={'num_predict': 5},
                    keep_alive=self.keep_alive_duration
                )

            warmup_time = int((time.time() - start) * 1000)
            self._is_warmed_up = True

            if self.enable_metrics:
                print(f"Model warmed up in {warmup_time} ms")

            return {'warmup_time_ms': warmup_time, 'model': self.model, 'keep_alive': self.keep_alive_duration}

        except ollama.ResponseError as e:
            print(f"Ollama API Error during warm-up: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during warm-up: {e}")
            raise

    def predict(
        self,
        image_path: str,
        auto_warmup: bool = True,
        show_visualization: Optional[bool] = None,
        show_metrics: Optional[bool] = None,
        resize: Optional[Union[int, tuple]] = None
    ) -> Dict:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        if auto_warmup and not self._is_warmed_up:
            self.warm_up(dummy_image_path=image_path)

        vis = show_visualization if show_visualization is not None else self.enable_visualization
        metrics = show_metrics if show_metrics is not None else self.enable_metrics

        image_path = os.path.abspath(image_path)

        original_image_path = image_path
        resized_image_path = None
        if resize is not None:
            resized_image_path = self._resize_image(image_path, resize)
            image_path = resized_image_path

        start = time.time()

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': self.prompt,
                    'images': [image_path]
                }],
                keep_alive=self.keep_alive_duration
            )

            end = time.time()

            raw_response = response['message']['content'].strip()
            pred_state = self._normalize_state(raw_response)

            wall_time_ms = int((end - start) * 1000)

            result = {
                "state": pred_state,
                "raw_response": raw_response,
                "model": self.model,
                "wall_time_ms": wall_time_ms,
                "model_was_loaded": self._is_warmed_up
            }

            if 'total_duration' in response:
                result['total_duration_ms'] = int(response['total_duration'] / 1_000_000)

            if 'load_duration' in response:
                load_ms = int(response['load_duration'] / 1_000_000)
                result['load_duration_ms'] = load_ms
                result['inference_only_ms'] = wall_time_ms - load_ms if load_ms > 0 else wall_time_ms
            else:
                result['inference_only_ms'] = wall_time_ms

            if 'prompt_eval_duration' in response:
                result['prompt_eval_duration_ms'] = int(response['prompt_eval_duration'] / 1_000_000)

            if 'eval_duration' in response:
                result['eval_duration_ms'] = int(response['eval_duration'] / 1_000_000)

            if 'prompt_eval_count' in response:
                result['prompt_tokens'] = response['prompt_eval_count']

            if 'eval_count' in response:
                result['completion_tokens'] = response['eval_count']

            if 'eval_count' in response and 'eval_duration' in response:
                eval_duration_s = response['eval_duration'] / 1_000_000_000
                if eval_duration_s > 0:
                    result['tokens_per_second'] = round(response['eval_count'] / eval_duration_s, 2)

            self._prediction_count += 1
            self._total_inference_time += result['inference_only_ms']

            return result

        except ollama.ResponseError as e:
            print(f"Ollama API Error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

    def _add_annotation_to_frame(
        self,
        frame: 'np.ndarray',
        pred_state: str,
        frame_num: int,
        inference_ms: int
    ):
        if not HAS_CV2:
            return

        height, width = frame.shape[:2]
        state_text = f"Frame {frame_num}: {pred_state.upper()} ({inference_ms}ms)"
        font = cv2.FONT_HERSHEY_SIMPLEX

        font_scale = max(0.8, width / 1000)
        thickness = max(2, int(width / 400))

        (text_width, text_height), baseline = cv2.getTextSize(
            state_text, font, font_scale, thickness
        )

        padding = 15
        cv2.rectangle(frame, (10, 10), (10 + text_width + padding * 2, 10 + text_height + padding * 2), (0, 0, 0), -1)
        cv2.putText(frame, state_text, (10 + padding, 10 + text_height + padding), font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)

    def batch_predict(
        self,
        image_dir: str,
        auto_warmup: bool = True,
        show_summary: bool = True,
        resize: Optional[Union[int, tuple]] = None
    ) -> List[Dict]:
        image_patterns = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
        image_files = []
        for pattern in image_patterns:
            image_files.extend(glob.glob(os.path.join(image_dir, pattern)))

        if not image_files:
            print(f"No images found in {image_dir}")
            return []

        if auto_warmup and not self._is_warmed_up:
            self.warm_up(dummy_image_path=image_files[0])

        results = []
        for img_path in image_files:
            try:
                result = self.predict(img_path, auto_warmup=False, show_visualization=False, show_metrics=False, resize=resize)
                results.append({'file': os.path.basename(img_path), 'path': img_path, 'state': result['state'], 'wall_time_ms': result['wall_time_ms'], 'inference_ms': result['inference_only_ms'], 'tokens_per_sec': result.get('tokens_per_second', 0)})
            except Exception as e:
                results.append({'file': os.path.basename(img_path), 'path': img_path, 'state': 'ERROR', 'wall_time_ms': 0, 'inference_ms': 0, 'tokens_per_sec': 0})

        return results

    def process_video(
        self,
        video_path: str,
        frame_interval: int = 1,
        auto_warmup: bool = True,
        show_visualization: bool = False,
        save_annotated_video: bool = True,
        output_video_path: Optional[str] = None,
        resize: Optional[Union[int, tuple]] = None,
        output_csv: Optional[str] = None
    ) -> List[Dict]:
        if not HAS_CV2:
            raise ImportError("OpenCV is required for video processing.")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Could not open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        video_writer = None
        if save_annotated_video and not show_visualization:
            if output_video_path is None:
                video_dir = os.path.dirname(video_path)
                name_without_ext = os.path.splitext(os.path.basename(video_path))[0]
                output_video_path = os.path.join(video_dir, f"{name_without_ext}_annotated.mp4")

            for codec_name, fourcc in [('avc1', cv2.VideoWriter_fourcc(*'avc1')), ('XVID', cv2.VideoWriter_fourcc(*'XVID')), ('mp4v', cv2.VideoWriter_fourcc(*'mp4v'))]:
                try:
                    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
                    if video_writer.isOpened():
                        break
                except:
                    continue

        if auto_warmup and not self._is_warmed_up:
            ret, first_frame = cap.read()
            if ret:
                temp_path = "temp_warmup_frame.jpg"
                cv2.imwrite(temp_path, first_frame)
                self.warm_up(dummy_image_path=temp_path)
                try:
                    os.remove(temp_path)
                except:
                    pass
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        results = []
        frame_num = 0
        temp_frame_path = "temp_frame.jpg"

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_num % frame_interval == 0:
                    cv2.imwrite(temp_frame_path, frame)

                    try:
                        result = self.predict(temp_frame_path, auto_warmup=False, show_visualization=False, show_metrics=False, resize=resize)
                        frame_result = {
                            'frame': frame_num,
                            'timestamp_sec': frame_num / fps if fps > 0 else 0,
                            'state': result['state'],
                            'inference_ms': result['inference_only_ms'],
                            'tokens_per_sec': result.get('tokens_per_second', 0)
                        }
                        results.append(frame_result)

                        if video_writer is not None:
                            annotated_frame = frame.copy()
                            self._add_annotation_to_frame(annotated_frame, result['state'], frame_num, result['inference_only_ms'])
                            video_writer.write(annotated_frame)

                    except Exception as e:
                        results.append({'frame': frame_num, 'timestamp_sec': frame_num / fps if fps > 0 else 0, 'state': 'ERROR', 'inference_ms': 0, 'tokens_per_sec': 0})

                frame_num += 1

        finally:
            cap.release()
            if video_writer is not None:
                video_writer.release()
            if show_visualization:
                cv2.destroyAllWindows()
            try:
                os.remove(temp_frame_path)
            except:
                pass

        if output_csv:
            try:
                import csv
                with open(output_csv, 'w', newline='') as f:
                    if results:
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
            except Exception as e:
                print(f"Warning: Could not save CSV: {e}")

        return results

    def describe_frame(self, image_path: str, resize: Optional[Union[int, tuple]] = None) -> Dict:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        original_image_path = image_path
        if resize is not None:
            resized = self._resize_image(image_path, resize)
            if resized:
                image_path = resized

        prompt = """You are an expert equine veterinarian analyzing a horse monitoring camera frame.
Provide a detailed description including: horse count and position, physical appearance, posture, current activity, behavioral indicators, and environmental context.
Be specific, objective, and use professional veterinary language.
Start directly with your observations."""

        start_time = time.time()

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt, 'images': [image_path]}],
                options={'temperature': 0.3, 'top_p': 0.9}
            )

            description = response['message']['content'].strip()
            generation_time_ms = int((time.time() - start_time) * 1000)

            return {
                'description': description,
                'image_path': original_image_path,
                'model_used': self.model,
                'generation_time_ms': generation_time_ms
            }

        except Exception as e:
            print(f"Error generating description: {e}")
            raise

    def get_stats(self) -> Dict:
        avg_inference_time = (
            self._total_inference_time / self._prediction_count
            if self._prediction_count > 0
            else 0
        )
        return {
            'model': self.model,
            'is_warmed_up': self._is_warmed_up,
            'prediction_count': self._prediction_count,
            'total_inference_time_ms': self._total_inference_time,
            'average_inference_time_ms': round(avg_inference_time, 2),
        }

    def __repr__(self) -> str:
        return f"HorseStateClassifier(model='{self.model}', warmed_up={self._is_warmed_up}, predictions={self._prediction_count})"
