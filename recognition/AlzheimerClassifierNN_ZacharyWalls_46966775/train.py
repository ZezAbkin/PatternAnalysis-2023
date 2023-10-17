import torch
import torch.nn as nn
import torch.optim as optim
from dataset import get_data_loaders
from modules import ViT
import matplotlib as plt

device = torch.device(
    "cpu"
    if torch.backends.mps.is_available()
    else "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

if __name__ == "__main__":
    # Load Data
    print(f"\nFETCHING DATA LOADERS\n{'='*25}\n")
    train_loader, test_loader = get_data_loaders()

    # Initialize Model
    print(f"\nINITIALIZING MODEL\n{'='*25}\n")
    num_labels = 2  # Alzheimer's or Normal
    model = ViT(num_classes=num_labels).to(device)
    print("Model ready.")

    # Define Loss, Optimizer and Scheduler
    lr = 0.000001
    wd = 0.1
    beta1 = 0.5
    beta2 = 0.999

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        model.parameters(), lr=lr, weight_decay=wd, betas=(beta1, beta2)
    )
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.9)

    # Training and Validation Loop
    num_epochs = 50
    best_val_accuracy = 0

    # Used for Graphing after Training
    val_losses = []
    val_accuracies = []

    print(f"\nTRAINING MODEL\n{'='*25}\n")
    for epoch in range(num_epochs):
        # Training Loop
        model.train()
        total_loss, total_correct, total_samples = 0, 0, len(train_loader.dataset)
        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)

            # Forward Pass
            logits = model(images)
            loss = criterion(logits, labels)

            # Backward Pass
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # Log Info
            pred = logits.argmax(dim=1)
            correct = pred.eq(labels).sum().item()
            total_loss += loss.item()
            total_correct += correct

            if batch_idx % 10 == 0:
                print(
                    f"Epoch {epoch}/{num_epochs}, Batch {batch_idx}/{len(train_loader)}, Training Loss: {loss.item()}, Training Accuracy: {correct / len(images)}"
                )

        train_accuracy = total_correct / total_samples
        print(
            f"Epoch {epoch}/{num_epochs}, Total Training Loss: {total_loss}, Total Training Accuracy: {train_accuracy}"
        )

        # Validation Loop
        model.eval()
        total_loss, total_correct, total_samples = 0, 0, len(test_loader.dataset)
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                pred = logits.argmax(dim=1)
                correct = pred.eq(labels).sum().item()
                total_loss += loss.item()
                total_correct += correct

        avg_val_loss = total_loss / total_samples
        val_accuracy = total_correct / total_samples

        print(
            f"Epoch {epoch}, Average Validation Loss: {avg_val_loss}, Total Validation Accuracy: {val_accuracy}\n"
        )

        val_losses.append(avg_val_loss)
        val_accuracies.append(val_accuracy)

        # Print the counters in a table format
        print("Validation Statistics:")
        print("-----------------------")
        print(f"|{'True AD (TP)':<25}|{TP:>5}|")
        print(f"|{'True NC (TN)':<25}|{TN:>5}|")
        print(f"|{'False AD (FP)':<25}|{FP:>5}|")
        print(f"|{'False NC (FN)':<25}|{FN:>5}|")
        print("-----------------------\n")

        # Step the scheduler
        scheduler.step()

        # Save the model with the highest validation accuracy
        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(model.state_dict(), "trained_model_weights.pth")
            print(f"Best Model Saved at Epoch {epoch}\n")

    # Plotting Validation Loss
    plt.figure(figsize=(12, 6))
    plt.plot(val_losses, label="Validation Loss", color="red")
    plt.xlabel("Epochs")
    plt.ylabel("Loss")
    plt.title("Validation Loss over Time")
    plt.legend()
    plt.show()

    # Plotting Validation Accuracy
    plt.figure(figsize=(12, 6))
    plt.plot(val_accuracies, label="Validation Accuracy", color="blue")
    plt.xlabel("Epochs")
    plt.ylabel("Accuracy")
    plt.title("Validation Accuracy over Time")
    plt.legend()
    plt.show()

    print("Training Completed!")
