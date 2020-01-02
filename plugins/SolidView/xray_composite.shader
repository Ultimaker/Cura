[shaders]
vertex =
    uniform highp mat4 u_modelViewProjectionMatrix;
    attribute highp vec4 a_vertex;
    attribute highp vec2 a_uvs;

    varying highp vec2 v_uvs;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        v_uvs = a_uvs;
    }

fragment =
    #ifdef GL_ES
        #ifdef GL_FRAGMENT_PRECISION_HIGH
            precision highp float;
        #else
            precision mediump float;
        #endif // GL_FRAGMENT_PRECISION_HIGH
    #endif // GL_ES
    uniform sampler2D u_layer0; //Default pass.
    uniform sampler2D u_layer1; //Selection pass.
    uniform sampler2D u_layer2; //X-ray pass.
    uniform sampler2D u_xray_error; //X-ray error image.

    uniform vec2 u_offset[9];

    uniform float u_outline_strength;
    uniform vec4 u_outline_color;
    uniform vec4 u_background_color;
    uniform float u_xray_error_strength;

    const vec3 x_axis = vec3(1.0, 0.0, 0.0);
    const vec3 y_axis = vec3(0.0, 1.0, 0.0);
    const vec3 z_axis = vec3(0.0, 0.0, 1.0);

    varying vec2 v_uvs;

    float kernel[9];

    float hash12(vec2 p)
    {
        vec2 pp = p * 1234.3;
        vec2 p2 = fract(pp) + fract(dot(pp, pp.yx + vec2(12.0,51.0)));
        return fract(fract(p2.x * p2.y) * 123.312);
    }

    void main()
    {
        kernel[0] = 0.0; kernel[1] = 1.0; kernel[2] = 0.0;
        kernel[3] = 1.0; kernel[4] = -4.0; kernel[5] = 1.0;
        kernel[6] = 0.0; kernel[7] = 1.0; kernel[8] = 0.0;

        vec4 result = u_background_color;
        vec4 layer0 = texture2D(u_layer0, v_uvs);

        result = layer0 * layer0.a + result * (1.0 - layer0.a);

        float intersection_count = texture2D(u_layer2, v_uvs).r * 255.0;
        if(mod(intersection_count, 2.0) >= 1.0)
        {
            vec2 scaling = textureSize(u_layer0, 0) / textureSize(u_xray_error, 0);
            result = result * (1.0 - u_xray_error_strength) + u_xray_error_strength * texture(u_xray_error, v_uvs * scaling);
        }

        vec4 sum = vec4(0.0);
        for (int i = 0; i < 9; i++)
        {
            vec4 color = vec4(texture2D(u_layer1, v_uvs.xy + u_offset[i]).a);
            sum += color * (kernel[i] / u_outline_strength);
        }

        vec4 layer1 = texture2D(u_layer1, v_uvs);
        if((layer1.rgb == x_axis || layer1.rgb == y_axis || layer1.rgb == z_axis))
        {
            gl_FragColor = result;
        }
        else
        {
            gl_FragColor = mix(result, u_outline_color, abs(sum.a));
        }

        gl_FragColor.a = gl_FragColor.a > 0.5 ? 1.0 : 0.0;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelViewProjectionMatrix;
    in highp vec4 a_vertex;
    in highp vec2 a_uvs;

    out highp vec2 v_uvs;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        v_uvs = a_uvs;
    }

fragment41core =
    #version 410
    uniform sampler2D u_layer0; //Default pass.
    uniform sampler2D u_layer1; //Selection pass.
    uniform sampler2D u_layer2; //X-ray pass.
    uniform sampler2D u_xray_error; //X-ray error image.

    uniform vec2 u_offset[9];

    uniform float u_outline_strength;
    uniform vec4 u_outline_color;
    uniform vec4 u_background_color;
    uniform float u_xray_error_strength;

    const vec3 x_axis = vec3(1.0, 0.0, 0.0);
    const vec3 y_axis = vec3(0.0, 1.0, 0.0);
    const vec3 z_axis = vec3(0.0, 0.0, 1.0);

    in vec2 v_uvs;
    out vec4 frag_color;

    float kernel[9];

    float hash12(vec2 p)
    {
        vec2 pp = p * 1234.3;
        vec2 p2 = fract(pp) + fract(dot(pp, pp.yx + vec2(12.0,51.0)));
        return fract(fract(p2.x * p2.y) * 123.312);
    }

    void main()
    {
        kernel[0] = 0.0; kernel[1] = 1.0; kernel[2] = 0.0;
        kernel[3] = 1.0; kernel[4] = -4.0; kernel[5] = 1.0;
        kernel[6] = 0.0; kernel[7] = 1.0; kernel[8] = 0.0;

        vec4 result = u_background_color;
        vec4 layer0 = texture(u_layer0, v_uvs);

        result = layer0 * layer0.a + result * (1.0 - layer0.a);

        float intersection_count = texture(u_layer2, v_uvs).r * 255.0;
        if(mod(intersection_count, 2.0) >= 1.0)
        {
            vec2 scaling = textureSize(u_layer0, 0) / textureSize(u_xray_error, 0);
            result = result * (1.0 - u_xray_error_strength) + u_xray_error_strength * texture(u_xray_error, v_uvs * scaling);
        }

        vec4 sum = vec4(0.0);
        for (int i = 0; i < 9; i++)
        {
            vec4 color = vec4(texture(u_layer1, v_uvs.xy + u_offset[i]).a);
            sum += color * (kernel[i] / u_outline_strength);
        }

        vec4 layer1 = texture(u_layer1, v_uvs);
        if((layer1.rgb == x_axis || layer1.rgb == y_axis || layer1.rgb == z_axis))
        {
            frag_color = result;
        }
        else
        {
            frag_color = mix(result, u_outline_color, abs(sum.a));
        }

        frag_color.a = frag_color.a > 0.5 ? 1.0 : 0.0;
    }

[defaults]
u_layer0 = 0
u_layer1 = 1
u_layer2 = 2
u_xray_error = 3
u_background_color = [0.965, 0.965, 0.965, 1.0]
u_outline_strength = 1.0
u_outline_color = [0.05, 0.66, 0.89, 1.0]
u_xray_error_strength = 0.4

[bindings]

[attributes]
a_vertex = vertex
a_uvs = uv

