using System;
using UnityEngine;

/// <summary>
/// Глобальная "шина шума": всё, что может услышать монстр (шаги, двери, подбор предметов),
/// вызывает Emit. MonsterAI подписывается и решает, идти ли проверять.
/// </summary>
public static class NoiseSystem
{
    public static event Action<Vector3, float> OnNoise;

    public static void Emit(Vector3 position, float radius)
    {
        OnNoise?.Invoke(position, radius);
    }
}

public interface IInteractable
{
    string Prompt { get; }
    bool CanInteract { get; }
    void Interact(PlayerController player);
}
