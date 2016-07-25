[shaders]
vertex =
    uniform highp mat4 u_viewProjectionMatrix;
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_normalMatrix;

    attribute highp vec4 a_vertex;
    attribute highp vec4 a_normal;
    attribute highp vec2 a_uvs;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;
    varying highp vec2 v_uvs;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_viewProjectionMatrix * world_space_vert;

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;

        v_uvs = a_uvs;
    }

fragment =
    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor;
    uniform highp vec3 u_lightPosition;
    uniform highp vec3 u_viewPosition;
    uniform mediump float u_opacity;
    uniform sampler2D u_texture;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;
    varying highp vec2 v_uvs;

    void main()
    {
        // Copied from platform.shader, removed texture
        mediump vec4 final_color = vec4(0.0);

        /* Ambient Component */
        final_color += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 light_dir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float n_dot_l = clamp(dot(normal, light_dir), 0.0, 1.0);
        final_color += (n_dot_l * u_diffuseColor);

        final_color.a = u_opacity;

        gl_FragColor = final_color;
    }

[defaults]
u_ambientColor = [0.3, 0.3, 0.3, 1.0]
u_diffuseColor = [1.0, 1.0, 1.0, 1.0]
u_opacity = 0.5
u_texture = 0

[bindings]
u_viewProjectionMatrix = view_projection_matrix
u_modelMatrix = model_matrix
u_normalMatrix = normal_matrix
u_lightPosition = light_0_position
u_viewPosition = camera_position

[attributes]
a_vertex = vertex
a_normal = normal
a_uvs = uv0
