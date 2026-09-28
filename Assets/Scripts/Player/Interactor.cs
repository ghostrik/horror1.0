using UnityEngine;

/// <summary>
/// Луч из центра камеры: находит двери, записки, батарейки. E — взаимодействовать.
/// </summary>
public class Interactor : MonoBehaviour
{
    public static Interactor Instance { get; private set; }

    public float distance = 2.3f;
    public PlayerController player;

    public IInteractable Current { get; private set; }

    void Awake() { Instance = this; }

    void Update()
    {
        Current = null;
        if (GameManager.Instance != null && !GameManager.Instance.IsPlaying) return;

        Ray ray = new Ray(transform.position, transform.forward);
        if (Physics.SphereCast(ray, 0.06f, out RaycastHit hit, distance, ~0, QueryTriggerInteraction.Ignore))
        {
            var target = hit.collider.GetComponentInParent<IInteractable>();
            if (target != null && target.CanInteract) Current = target;
        }

        if (Current != null && (HInput.KeyDown(KeyCode.E) || HInput.KeyDown(KeyCode.Mouse0)))
            Current.Interact(player);
    }
}
