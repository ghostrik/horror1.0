using UnityEngine;

/// <summary>Предохранитель для щитка гипермаркета.</summary>
public class FusePickup : MonoBehaviour, IInteractable
{
    public AudioClip pickupClip;

    public string Prompt => "[E] Взять предохранитель";
    public bool CanInteract => true;

    public void Interact(PlayerController player)
    {
        if (pickupClip != null) AudioSource.PlayClipAtPoint(pickupClip, transform.position, 0.9f);
        NoiseSystem.Emit(transform.position, 3f);
        gameObject.SetActive(false);
        if (GameManager.Instance != null) GameManager.Instance.OnFuseCollected();
    }
}
