using UnityEngine;

/// <summary>
/// Пыль, висящая в воздухе вокруг игрока. Видна в луче фонаря.
/// Система частиц создаётся и настраивается из кода, материал задаётся в инспекторе.
/// </summary>
public class DustMotes : MonoBehaviour
{
    public Material dustMaterial;
    public Transform follow;
    public int maxParticles = 260;
    public float radius = 6f;

    ParticleSystem ps;

    void Awake()
    {
        ps = GetComponent<ParticleSystem>();
        if (ps == null) ps = gameObject.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);

        var main = ps.main;
        main.loop = true;
        main.playOnAwake = true;
        main.startLifetime = new ParticleSystem.MinMaxCurve(6f, 12f);
        main.startSpeed = new ParticleSystem.MinMaxCurve(0.01f, 0.05f);
        main.startSize = new ParticleSystem.MinMaxCurve(0.006f, 0.02f);
        main.startColor = new Color(0.9f, 0.88f, 0.8f, 0.5f);
        main.maxParticles = maxParticles;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.gravityModifier = 0.002f;

        var emission = ps.emission;
        emission.rateOverTime = maxParticles / 9f;

        var shape = ps.shape;
        shape.shapeType = ParticleSystemShapeType.Sphere;
        shape.radius = radius;

        var noise = ps.noise;
        noise.enabled = true;
        noise.strength = 0.06f;
        noise.frequency = 0.3f;
        noise.scrollSpeed = 0.1f;

        var col = ps.colorOverLifetime;
        col.enabled = true;
        var grad = new Gradient();
        grad.SetKeys(
            new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
            new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.25f), new GradientAlphaKey(1f, 0.75f), new GradientAlphaKey(0f, 1f) });
        col.color = grad;

        var rend = GetComponent<ParticleSystemRenderer>();
        rend.renderMode = ParticleSystemRenderMode.Billboard;
        if (dustMaterial != null) rend.sharedMaterial = dustMaterial;

        ps.Play();
    }

    void LateUpdate()
    {
        if (follow != null) transform.position = follow.position;
    }
}
