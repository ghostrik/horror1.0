using UnityEngine;

/// <summary>Предмет лора: чек, VHS-кассета, служебная записка. Читается по E, засчитывается в находки.</summary>
public class NotePickup : MonoBehaviour, IInteractable
{
    public int order = 1;
    public string title = "Записка";
    public string prompt = "[E] Прочитать";
    [TextArea(6, 20)] public string body = "";

    public bool Collected { get; private set; }
    public string Prompt => prompt;
    public bool CanInteract => !Collected;

    public void Interact(PlayerController player)
    {
        if (GameManager.Instance != null) GameManager.Instance.ReadNote(this);
        NoiseSystem.Emit(transform.position, 2.5f);
    }

    public void Collect()
    {
        Collected = true;
        gameObject.SetActive(false);
    }
}
