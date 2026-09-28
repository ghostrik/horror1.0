// Полупрозрачная наклейка на поверхность: грязь, пятна, граффити, лужи, следы.
// Кладётся на Quad чуть над поверхностью; Offset убирает мерцание.
Shader "Horror/Decal"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo (A = маска)", 2D) = "white" {}
        _Glossiness ("Smoothness", Range(0,1)) = 0.4
    }
    SubShader
    {
        Tags { "Queue"="AlphaTest+50" "RenderType"="Transparent" "IgnoreProjector"="True" "ForceNoShadowCasting"="True" }
        LOD 200
        Offset -1, -1
        ZWrite Off

        CGPROGRAM
        #pragma surface surf Standard decal:blend
        #pragma target 3.0

        sampler2D _MainTex;
        fixed4 _Color;
        half _Glossiness;

        struct Input { float2 uv_MainTex; };

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = c.rgb;
            o.Smoothness = _Glossiness * c.a;
            o.Alpha = c.a;
        }
        ENDCG
    }
    FallBack Off
}
