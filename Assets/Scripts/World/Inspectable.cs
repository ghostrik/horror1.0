using UnityEngine;

/// <summary>Предмет, который можно только осмотреть (надпись, фото, вещь).</summary>
public class Inspectable : MonoBehaviour, IInteractable
{
    public string promptText = "[E] Осмотреть";
    [TextArea(2, 6)] public string description = "";

    public string Prompt => promptText;
    public bool CanInteract => true;

    public void Interact(PlayerController player)
    {
        if (GameManager.Instance != null) GameManager.Instance.ShowMessage(description, 4f);
    }
}
