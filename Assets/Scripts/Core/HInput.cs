using UnityEngine;
#if ENABLE_INPUT_SYSTEM && !ENABLE_LEGACY_INPUT_MANAGER
using UnityEngine.InputSystem;
using IKey = UnityEngine.InputSystem.Key;
#endif

/// <summary>
/// Тонкая обёртка над вводом. Работает и со старым Input Manager,
/// и с новым Input System (если в проекте включён только он).
/// </summary>
public static class HInput
{
#if ENABLE_INPUT_SYSTEM && !ENABLE_LEGACY_INPUT_MANAGER
    static IKey Map(KeyCode k)
    {
        switch (k)
        {
            case KeyCode.W: return IKey.W;
            case KeyCode.A: return IKey.A;
            case KeyCode.S: return IKey.S;
            case KeyCode.D: return IKey.D;
            case KeyCode.E: return IKey.E;
            case KeyCode.F: return IKey.F;
            case KeyCode.R: return IKey.R;
            case KeyCode.C: return IKey.C;
            case KeyCode.M: return IKey.M;
            case KeyCode.Tab: return IKey.Tab;
            case KeyCode.Space: return IKey.Space;
            case KeyCode.Return: return IKey.Enter;
            case KeyCode.Escape: return IKey.Escape;
            case KeyCode.LeftShift: return IKey.LeftShift;
            case KeyCode.LeftControl: return IKey.LeftCtrl;
            case KeyCode.UpArrow: return IKey.UpArrow;
            case KeyCode.DownArrow: return IKey.DownArrow;
            case KeyCode.LeftArrow: return IKey.LeftArrow;
            case KeyCode.RightArrow: return IKey.RightArrow;
            default: return IKey.None;
        }
    }

    public static bool Key(KeyCode k)
    {
        var kb = Keyboard.current;
        if (kb == null) return false;
        if (k == KeyCode.Mouse0) return Mouse.current != null && Mouse.current.leftButton.isPressed;
        var key = Map(k);
        return key != IKey.None && kb[key].isPressed;
    }

    public static bool KeyDown(KeyCode k)
    {
        var kb = Keyboard.current;
        if (kb == null) return false;
        if (k == KeyCode.Mouse0) return Mouse.current != null && Mouse.current.leftButton.wasPressedThisFrame;
        var key = Map(k);
        return key != IKey.None && kb[key].wasPressedThisFrame;
    }

    public static Vector2 Look()
    {
        var m = Mouse.current;
        return m == null ? Vector2.zero : m.delta.ReadValue() * 0.05f;
    }
#else
    public static bool Key(KeyCode k) => Input.GetKey(k);
    public static bool KeyDown(KeyCode k) => Input.GetKeyDown(k);

    public static Vector2 Look() => new Vector2(Input.GetAxisRaw("Mouse X"), Input.GetAxisRaw("Mouse Y"));
#endif

    public static Vector2 Move()
    {
        float x = 0f, y = 0f;
        if (Key(KeyCode.W) || Key(KeyCode.UpArrow)) y += 1f;
        if (Key(KeyCode.S) || Key(KeyCode.DownArrow)) y -= 1f;
        if (Key(KeyCode.D) || Key(KeyCode.RightArrow)) x += 1f;
        if (Key(KeyCode.A) || Key(KeyCode.LeftArrow)) x -= 1f;
        return Vector2.ClampMagnitude(new Vector2(x, y), 1f);
    }

    public static void LockCursor(bool locked)
    {
        Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !locked;
    }
}
