import os
import sys
import argparse
import json
import sys

# Import deeplabcut globally to initialize the module correctly
import deeplabcut
print(f"DEBUG: deeplabcut loaded from: {deeplabcut.__file__}")
if not hasattr(deeplabcut, 'analyze_videos'):
    print(f"DEBUG: No analyze_videos! dir: {dir(deeplabcut)}")

def process_video(video_path, config_path, shuffle=4):
    print(f"Loading DeepLabCut model from config: {config_path}")
    print(f"Processing video: {video_path} with shuffle={shuffle}")

    # Reduce TensorFlow/PyTorch log spam
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    # Add app directory to path so imports work
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app.services.behavior_analysis_service import BehaviorAnalysisService
    
    try:
        service = BehaviorAnalysisService(
            config_path=config_path,
            results_folder=os.path.dirname(video_path)
        )
        
        # Analyze video and get behavior overlay
        result = service.analyze_video_with_behavior(
            video_path=video_path,
            show_keypoints=True,
            lying_height_ratio_threshold=0.6,
            eating_height_ratio_threshold=0.8,
            drinking_height_ratio_threshold=0.6,
            movement_threshold=15.0,
            likelihood_threshold=0.5,
            shuffle=shuffle,
            device='cuda:0'
        )

        if result.get("status") == "success":
            print("\nSuccess! A new video with keypoints drawn has been saved.")
            # Print JSON string for the backend to parse
            print(f"__DLC_JSON_RESULT__={json.dumps(result)}")
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(0)
        else:
            print(f"Analysis failed: {result.get('message', 'Unknown error')}")
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(1)

    except Exception as e:
        print(f"DeepLabCut pipeline failed: {e}")
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DeepLabCut directly on a video to draw keypoints and classify behaviors")
    parser.add_argument("video", help="Full path to the video file you want to analyze")
    parser.add_argument(
        "--config",
        default=r"E:\Graduation_project_repo\ModernizeStables\DeepLabCut\finetuning-agamy-2025-10-15\finetune_superAnimal-agamy-2025-10-22\config.yaml",
        help="Path to your DeepLabCut project config.yaml"
    )
    parser.add_argument("--shuffle", type=int, default=4, help="Which model shuffle to use (default: 4)")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)

    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)

    process_video(os.path.abspath(args.video), os.path.abspath(args.config), args.shuffle)

