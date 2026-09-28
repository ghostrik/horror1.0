// Мировой трипланарный шейдер для статичной геометрии уровня.
// Текстура кладётся по мировым координатам, поэтому стены/пол любого размера
// выглядят одинаково без UV-развёртки. Опционально — вторая текстура "панели" снизу стены.
Shader "Horror/WorldTriplanar"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo", 2D) = "white" {}
        _BumpMap ("Normal", 2D) = "bump" {}
        _BumpScale ("Normal Strength", Float) = 1
        _Scale ("World Scale (repeats per meter)", Float) = 0.5
        _Glossiness ("Smoothness", Range(0,1)) = 0.2
        _Metallic ("Metallic", Range(0,1)) = 0
        _LowerTex ("Lower Panel Albedo", 2D) = "white" {}
        _LowerColor ("Lower Panel Color", Color) = (1,1,1,1)
        _LowerHeight ("Lower Panel Height (0 = off)", Float) = 0
        _LowerScale ("Lower Panel Scale", Float) = 1
        _LowerGloss ("Lower Panel Smoothness", Range(0,1)) = 0.5
        _GrimeHeight ("Floor Grime Height", Float) = 0.4
        _GrimeStrength ("Floor Grime Strength", Range(0,1)) = 0.4
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 300

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0

        sampler2D _MainTex, _BumpMap, _LowerTex;
        fixed4 _Color, _LowerColor;
        half _Scale, _Glossiness, _Metallic, _BumpScale, _LowerHeight, _LowerScale, _LowerGloss, _GrimeHeight, _GrimeStrength;

        struct Input
        {
            float3 worldPos;
            float3 worldNormal;
            INTERNAL_DATA
        };

        float3 BlendWeights(float3 n)
        {
            float3 w = pow(abs(n), 6.0);
            return w / (w.x + w.y + w.z + 1e-5);
        }

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            float3 n = WorldNormalVector(IN, float3(0,0,1));
            float3 w = BlendWeights(n);
            float3 p = IN.worldPos;

            float2 uvX = p.zy * _Scale;
            float2 uvY = p.xz * _Scale;
            float2 uvZ = p.xy * _Scale;

            fixed4 cx = tex2D(_MainTex, uvX);
            fixed4 cy = tex2D(_MainTex, uvY);
            fixed4 cz = tex2D(_MainTex, uvZ);
            fixed4 c = (cx * w.x + cy * w.y + cz * w.z) * _Color;
            half gloss = _Glossiness;

            if (_LowerHeight > 0.0 && p.y < _LowerHeight && w.y < 0.5)
            {
                float2 lx = p.zy * _LowerScale;
                float2 lz = p.xy * _LowerScale;
                fixed4 lc = (tex2D(_LowerTex, lx) * w.x + tex2D(_LowerTex, lz) * w.z) / max(w.x + w.z, 1e-3);
                c = lc * _LowerColor;
                gloss = _LowerGloss;
                // тёмная полоса-бордюр по верху панели
                c.rgb *= lerp(0.35, 1.0, smoothstep(0.0, 0.04, _LowerHeight - p.y));
            }

            // грязь у самого пола
            if (w.y < 0.5)
                c.rgb *= lerp(1.0 - _GrimeStrength, 1.0, saturate(p.y / max(_GrimeHeight, 0.01)));

            half3 nx = UnpackScaleNormal(tex2D(_BumpMap, uvX), _BumpScale);
            half3 ny = UnpackScaleNormal(tex2D(_BumpMap, uvY), _BumpScale);
            half3 nz = UnpackScaleNormal(tex2D(_BumpMap, uvZ), _BumpScale);

            o.Albedo = c.rgb;
            o.Normal = normalize(nx * w.x + ny * w.y + nz * w.z);
            o.Metallic = _Metallic;
            o.Smoothness = gloss * c.a;
            o.Alpha = 1;
        }
        ENDCG
    }
    FallBack "Diffuse"
}
