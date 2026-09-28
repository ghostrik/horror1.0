using UnityEngine;

/// <summary>
/// Укрытие (фотобудка, шкафчик, примерочная). E — залезть, E — вылезти.
/// Если Мерчандайзер не видел, как ты залез, — он тебя не найдёт.
/// </summary>
public class HidingSpot : MonoBehaviour, IInteractable
{
    public Transform hidePoint;
    public Transform exitPoint;
    public string hidePrompt = "[E] Спрятаться";
    public AudioSource source;
    public AudioClip enterClip;
    public AudioClip exitClip;

    public bool Occupied { get; private set; }
    public string Prompt => hidePrompt;
    public bool CanInteract => !Occupied;

    PlayerController player;
    float enterTime;

    void Awake()
    {
        if (source != null) { source.spatialBlend = 1f; source.playOnAwake = false; }
    }

    public void Interact(PlayerController p)
    {
        if (Occupied || p == null || hidePoint == null) return;
        player = p;
        Occupied = true;
        enterTime = Time.time;

        var cc = p.GetComponent<CharacterController>();
        if (cc != null) cc.enabled = false;
        p.transform.position = hidePoint.position;
        p.SetLookRotation(hidePoint.rotation);
        p.IsHidden = true;
        if (source != null && enterClip != null) source.PlayOneShot(enterClip, 0.7f);
        NoiseSystem.Emit(transform.position, 4f);
        if (GameManager.Instance != null) GameManager.Instance.ShowMessage("Сиди тихо. [E] — вылезти.", 2.5f);
    }

    void Update()
    {
        if (!Occupied || player == null) return;
        if (GameManager.Instance != null && !GameManager.Instance.IsPlaying) return;
        if (Time.time - enterTime < 0.35f) return;
        if (HInput.KeyDown(KeyCode.E)) Leave();
    }

    public void Leave()
    {
        if (!Occupied || player == null) return;
        Transform to = exitPoint != null ? exitPoint : transform;
        player.transform.position = to.position;
        player.SetLookRotation(to.rotation);
        var cc = player.GetComponent<CharacterController>();
        if (cc != null) cc.enabled = true;
        player.IsHidden = false;
        if (source != null && exitClip != null) source.PlayOneShot(exitClip, 0.7f);
        NoiseSystem.Emit(transform.position, 4f);
        Occupied = false;
        player = null;
    }
}
