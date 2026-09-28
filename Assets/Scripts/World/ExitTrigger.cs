using UnityEngine;

/// <summary>Зона выхода: зайдёшь после включения питания — конец демо.</summary>
public class ExitTrigger : MonoBehaviour
{
    bool done;

    void OnTriggerEnter(Collider other)
    {
        if (done || other.GetComponentInParent<PlayerController>() == null) return;
        if (GameManager.Instance == null || !GameManager.Instance.PowerRestored) return;
        done = true;
        GameManager.Instance.ReachedExit();
    }
}
