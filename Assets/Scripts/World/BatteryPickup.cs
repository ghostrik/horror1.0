using UnityEngine;

/// <summary>Батарейка для фонарика.</summary>
public class BatteryPickup : MonoBehaviour, IInteractable
{
    [Range(0f, 1f)] public float charge = 0.5f;
    public AudioClip pickupClip;

    public string Prompt => "[E] Взять батарейку";
    public bool CanInteract => true;

    float baseY;

    void Start() { baseY = transform.position.y; }

    void Update()
    {
        // лёгкое мерцание-подсказка: чуть покачивается
        Vector3 p = transform.position;
        p.y = baseY + Mathf.Sin(Time.time * 2f) * 0.01f;
        transform.position = p;
    }

    public void Interact(PlayerController player)
    {
        if (Flashlight.Instance != null) Flashlight.Instance.AddBattery(charge);
        if (pickupClip != null) AudioSource.PlayClipAtPoint(pickupClip, transform.position, 0.8f);
        if (GameManager.Instance != null) GameManager.Instance.ShowMessage("Батарейка. Фонарь протянет ещё немного.", 2.5f);
        gameObject.SetActive(false);
    }
}
