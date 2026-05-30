import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms
from torchvision.models import resnet18, ResNet18_Weights

from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

INPUT_DIR = "/kaggle/input/datasets/ursadityasharma/skin-cancer-detection"

CSV_PATH = os.path.join(INPUT_DIR, "final_labels.csv")

IMAGE_DIR = os.path.join(INPUT_DIR, "images/images")

MODEL_DIR = "/kaggle/working/models"

BATCH_SIZE = 32
EPOCHS = 1
LR = 1e-4

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print("Using device:", DEVICE)

print("Images folder exists:", os.path.exists(IMAGE_DIR))

print("Total images:", len(os.listdir(IMAGE_DIR)))

print(os.listdir(IMAGE_DIR)[:5])
df = pd.read_csv(CSV_PATH)

print("Original CSV size:", len(df))

print(df["image_path"].head())

df["image_path"] = df["image_path"].apply(
    lambda x: os.path.join(IMAGE_DIR, os.path.basename(x))
)

print("\nChecking paths:\n")

for i in range(5):

    p = df["image_path"].iloc[i]

    print(p)
    print(os.path.exists(p))
    print("-" * 40)

df = df[df["image_path"].apply(os.path.exists)].reset_index(drop=True)

print("\nFinal dataset size:", len(df))

print("\nClass distribution:\n")

print(df["label"].value_counts())
sample_img = Image.open(df["image_path"].iloc[0])

plt.figure(figsize=(5,5))

plt.imshow(sample_img)

plt.title(df["label"].iloc[0])

plt.axis("off")

plt.show()
train_df, val_df = train_test_split(
    df,
    test_size=0.2,
    stratify=df["label"],
    random_state=42
)

class SkinDataset(Dataset):

    def __init__(self, df, transform=None):

        self.df = df.reset_index(drop=True)

        self.transform = transform

        self.label_map = {
            "nevus": 0,
            "melanoma": 1,
            "bcc": 2,
            "other": 3
        }

    def __len__(self):

        return len(self.df)

    def __getitem__(self, idx):

        row = self.df.iloc[idx]

        image = Image.open(row["image_path"]).convert("RGB")

        label = self.label_map[row["label"]]

        if self.transform:
            image = self.transform(image)

        return image, label

train_transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor()
])

val_transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor()
])

train_dataset = SkinDataset(train_df, train_transform)

val_dataset = SkinDataset(val_df, val_transform)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

print("Train batches:", len(train_loader))
print("Validation batches:", len(val_loader))
images, labels = next(iter(train_loader))

print("Images shape:", images.shape)

print("Labels shape:", labels.shape)

model = resnet18(weights=ResNet18_Weights.DEFAULT)

model.fc = torch.nn.Linear(model.fc.in_features, 4)

model = model.to(DEVICE)

images = images.to(DEVICE)

outputs = model(images)

print("Outputs shape:", outputs.shape)

print("\n✅ Pipeline working!")
# ================= TRAINING WITH EARLY STOPPING =================

import copy

criterion = torch.nn.CrossEntropyLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=1e-4
)

# ================= SETTINGS =================

EPOCHS = 8

PATIENCE = 2

best_acc = 0.0

epochs_without_improvement = 0

best_model_path = "/kaggle/working/best_skin_model.pt"

print("\nStarting training...\n")

for epoch in range(EPOCHS):

    print(f"\n================ EPOCH {epoch+1}/{EPOCHS} ================\n")

    # ================= TRAIN =================

    model.train()

    total_loss = 0

    epoch_start = time.time()

    for batch_idx, (images, labels) in enumerate(train_loader):

        images = images.to(DEVICE)

        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        total_loss += loss.item()

        # PRINT EVERY 10 BATCHES
        if batch_idx % 10 == 0:

            print(
                f"Batch {batch_idx}/{len(train_loader)} | "
                f"Loss: {loss.item():.4f}"
            )

    print(f"\nEpoch Training Loss: {total_loss:.4f}")

    print(f"Epoch Time: {time.time()-epoch_start:.2f}s")

    # ================= VALIDATION =================

    print("\nRunning validation...\n")

    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in val_loader:

            images = images.to(DEVICE)

            labels = labels.to(DEVICE)

            outputs = model(images)

            _, preds = torch.max(outputs, 1)

            correct += (preds == labels).sum().item()

            total += labels.size(0)

    val_acc = 100 * correct / total

    print(f"\n✅ Validation Accuracy: {val_acc:.2f}%")

    # ================= SAVE BEST MODEL =================

    if val_acc > best_acc:

        print("\n🔥 Validation improved!")

        best_acc = val_acc

        epochs_without_improvement = 0

        torch.save(model.state_dict(), best_model_path)

        print(f"✅ Best model saved!")
        print(f"✅ Best Accuracy: {best_acc:.2f}%")

    else:

        epochs_without_improvement += 1

        print(
            f"\n⚠️ No improvement for "
            f"{epochs_without_improvement} epoch(s)"
        )

    # ================= EARLY STOPPING =================

    if epochs_without_improvement >= PATIENCE:

        print("\n🛑 Early stopping triggered!")

        break

# ================= FINAL SUMMARY =================

print("\n================ TRAINING COMPLETE ================\n")

print(f"🏆 Best Validation Accuracy: {best_acc:.2f}%")

print(f"\n📁 Best model saved at:")

print(best_model_path)
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns

all_preds = []
all_labels = []

model.eval()

with torch.no_grad():

    for images, labels in val_loader:

        images = images.to(DEVICE)

        outputs = model(images)

        _, preds = torch.max(outputs, 1)

        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.numpy())

# ================= LABEL NAMES =================

label_names = ["nevus", "melanoma", "bcc", "other"]

# ================= CONFUSION MATRIX =================

cm = confusion_matrix(all_labels, all_preds)

plt.figure(figsize=(8,6))

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Blues",
    xticklabels=label_names,
    yticklabels=label_names
)

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")

plt.show()

# ================= CLASSIFICATION REPORT =================

print("\nClassification Report:\n")

print(classification_report(
    all_labels,
    all_preds,
    target_names=label_names
))
import matplotlib.pyplot as plt

label_names = ["nevus", "melanoma", "bcc", "other"]

model.eval()

shown = 0

plt.figure(figsize=(15,15))

with torch.no_grad():

    for images, labels in val_loader:

        images = images.to(DEVICE)

        outputs = model(images)

        probs = torch.softmax(outputs, dim=1)

        confs, preds = torch.max(probs, 1)

        for i in range(len(images)):

            actual = labels[i].item()

            pred = preds[i].item()

            conf = confs[i].item()

            # SHOW ONLY WRONG HIGH-CONFIDENCE PREDICTIONS
            if pred != actual and conf > 0.90:

                shown += 1

                img = images[i].cpu().permute(1,2,0).numpy()

                plt.subplot(4,4,shown)

                plt.imshow(img)

                plt.title(
                    f"A:{label_names[actual]}\n"
                    f"P:{label_names[pred]}\n"
                    f"C:{conf:.2f}"
                )

                plt.axis("off")

            if shown >= 16:
                break

        if shown >= 16:
            break

plt.tight_layout()
plt.show()
