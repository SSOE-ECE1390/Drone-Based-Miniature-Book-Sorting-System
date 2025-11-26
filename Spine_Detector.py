import os
from ultralytics import YOLO


class SpineDetectorTrainer:
    def __init__(self, dataset_path):
        """
        Initialize YOLO trainer for book spine detection.

        Args:
            dataset_path: Path to dataset folder containing:
                - images/
                    - train/
                    - val/  (or test/)
                - labels/
                    - train/
                    - val/
                - data.yaml (dataset configuration)
        """
        self.dataset_path = dataset_path
        self.model = None
        self.trained_model_path = None

        # Verify dataset structure
        self._verify_dataset()

    def _verify_dataset(self):
        """Check that dataset has required structure."""
        train_path = os.path.join(self.dataset_path, "train")
        test_path = os.path.join(self.dataset_path, "test")

        for path in [train_path, test_path]:
            if os.path.exists(path):
                num_images = len(
                    [
                        f
                        for f in os.listdir(path)
                        if f.endswith((".jpg", ".jpeg", ".png"))
                    ]
                )
                print(f"Found {num_images} images in {path}")
            else:
                print(f"WARNING: Missing directory {path}")

        yaml_path = os.path.join(self.dataset_path, "data.yaml")
        if not os.path.exists(yaml_path):
            print(f"WARNING: data.yaml not found at {yaml_path}")
        else:
            print(f"Found dataset config: {yaml_path}")

    def create_data_yaml(self, class_names=["spine"], output_path=None):
        """Create data.yaml configuration file for YOLO training."""
        if output_path is None:
            output_path = os.path.join(self.dataset_path, "data.yaml")

        yaml_content = f"""path: {os.path.abspath(self.dataset_path)}
train: train
val: test

names:
"""
        for i, name in enumerate(class_names):
            yaml_content += f"  {i}: {name}\n"

        with open(output_path, "w") as f:
            f.write(yaml_content)

        print(f"Created data.yaml at {output_path}")
        return output_path

    def train(
        self,
        epochs=100,
        imgsz=640,
        batch=16,
        model_size="n",
        project="runs/train",
        name="spine_detector",
    ):
        """
        Train YOLO model on the spine detection dataset.

        Args:
            epochs: Number of training epochs (100 is good starting point)
            imgsz: Image size for training (640 is standard)
            batch: Batch size (reduce if you get OOM errors)
            model_size: YOLO model size - 'n'(nano), 's'(small), 'm'(medium), 'l'(large), 'x'(xlarge)
                       Start with 'n' or 's' for faster training, use larger for better accuracy
            project: Directory to save training runs
            name: Name for this training run

        Returns:
            Path to best trained model weights
        """
        # Initialize base model
        base_model = f"yolov8{model_size}.pt"
        print(f"Loading base model: {base_model}")
        self.model = YOLO(base_model)

        # Path to data.yaml
        data_yaml = os.path.join(self.dataset_path, "data.yaml")

        if not os.path.exists(data_yaml):
            raise FileNotFoundError(
                f"data.yaml not found at {data_yaml}. "
                "Run create_data_yaml() first or check your Roboflow export."
            )

        print(f"\nStarting training...")
        print(f"  Dataset: {data_yaml}")
        print(f"  Epochs: {epochs}")
        print(f"  Image size: {imgsz}")
        print(f"  Batch size: {batch}")
        print(f"  Model: YOLOv8{model_size}")
        print("\nThis may take a while on CPU. Consider using Google Colab with GPU.\n")

        # Train the model
        results = self.model.train(
            data=data_yaml,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            project=project,
            name=name,
            patience=20,  # Early stopping if no improvement for 20 epochs
            save=True,
            plots=True,  # Save training plots
            verbose=True,
        )

        # Path to best weights
        self.trained_model_path = os.path.join(project, name, "weights", "best.pt")

        print(f"\nTraining complete!")
        print(f"Best model saved to: {self.trained_model_path}")
        print(f"Training results saved to: {os.path.join(project, name)}")

        return self.trained_model_path

    def evaluate(self, model_path=None):
        """
        Evaluate trained model on validation set.

        Args:
            model_path: Path to model weights (uses last trained if None)
        """
        if model_path is None:
            model_path = self.trained_model_path

        if model_path is None:
            raise ValueError(
                "No model path provided and no model has been trained yet."
            )

        model = YOLO(model_path)
        data_yaml = os.path.join(self.dataset_path, "data.yaml")

        print(f"Evaluating model: {model_path}")
        results = model.val(data=data_yaml)

        print("\nEvaluation Results:")
        print(f"  mAP50: {results.box.map50:.4f}")
        print(f"  mAP50-95: {results.box.map:.4f}")
        print(f"  Precision: {results.box.mp:.4f}")
        print(f"  Recall: {results.box.mr:.4f}")

        return results

    def test_on_image(self, image_path, model_path=None, save_result=True):
        """
        Test trained model on a single image.

        Args:
            image_path: Path to test image
            model_path: Path to model weights
            save_result: Whether to save annotated image
        """
        if model_path is None:
            model_path = self.trained_model_path

        if model_path is None:
            raise ValueError(
                "No model path provided and no model has been trained yet."
            )

        model = YOLO(model_path)

        results = model(image_path)

        # Print detections
        for result in results:
            boxes = result.boxes
            print(f"\nDetected {len(boxes)} objects in {image_path}")

            for i, box in enumerate(boxes):
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                print(
                    f"  Object {i}: class={cls}, conf={conf:.2f}, "
                    f"bbox=({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})"
                )

        if save_result:
            # Save annotated image
            output_path = image_path.replace(".jpg", "_detected.jpg")
            results[0].save(output_path)
            print(f"Saved annotated image to: {output_path}")

        return results

    def export_model(self, model_path=None, format="onnx"):
        """
        Export model to different format for deployment.

        Args:
            model_path: Path to model weights
            format: Export format ('onnx', 'torchscript', 'tflite', etc.)
        """
        if model_path is None:
            model_path = self.trained_model_path

        model = YOLO(model_path)
        exported_path = model.export(format=format)

        print(f"Model exported to: {exported_path}")
        return exported_path


if __name__ == "__main__":
    trainer = SpineDetectorTrainer("C:/Images/Bookshelf recognition.v1i.yolov8")

    best_model = trainer.train(
        epochs=50, imgsz=640, batch=8, model_size="n", name="spine_v1"
    )

    trainer.evaluate()
    trainer.test_on_image("Drone Image.jpg")

    print(f"\nTrained model saved to: {best_model}")
    print(
        "Use in ShelfReader: ShelfReader(yolo_model_path='runs/train/spine_v1/weights/best.pt')"
    )
