using UnityEngine;

/// <summary>Рольставня: поднимается вверх с дребезжанием, когда дали питание.</summary>
public class RollingShutter : MonoBehaviour, IInteractable
{
    public Transform panel;
    public float openHeight = 2.6f;
    public float speed = 0.45f;
    public AudioSource source;
    public AudioClip rattleClip;
    [TextArea] public string closedMessage = "Рольставня. Без электричества не поднять.";

    public bool IsOpen { get; private set; }
    public string Prompt => "[E] Поднять рольставню";
    public bool CanInteract => !IsOpen;

    Vector3 closedPos;
    float t;

    void Awake()
    {
        if (panel == null) panel = transform;
        closedPos = panel.localPosition;
        if (source != null) { source.spatialBlend = 1f; source.playOnAwake = false; }
    }

    public void Interact(PlayerController player)
    {
        if (GameManager.Instance != null) GameManager.Instance.ShowMessage(closedMessage);
        if (source != null && rattleClip != null) source.PlayOneShot(rattleClip, 0.4f);
        NoiseSystem.Emit(transform.position, 6f);
    }

    public void Open()
    {
        if (IsOpen) return;
        IsOpen = true;
        if (source != null && rattleClip != null) source.PlayOneShot(rattleClip, 1f);
    }

    void Update()
    {
        if (!IsOpen || t >= 1f) return;
        t = Mathf.MoveTowards(t, 1f, Time.deltaTime * speed);
        float shake = (1f - t) * Mathf.Sin(Time.time * 60f) * 0.01f;
        panel.localPosition = closedPos + Vector3.up * (openHeight * Mathf.SmoothStep(0f, 1f, t) + shake);
    }
}
