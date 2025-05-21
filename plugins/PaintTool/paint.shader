[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

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
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

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
        mediump vec4 final_color = vec4(0.0);

        /* Ambient Component */
        final_color += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 light_dir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float n_dot_l = clamp(dot(normal, light_dir), 0.0, 1.0);
        final_color += (n_dot_l * u_diffuseColor);

        final_color.a = u_opacity;

        lowp vec4 texture = texture2D(u_texture, v_uvs);
        final_color = mix(final_color, texture, texture.a);

        gl_FragColor = final_color;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform highp mat4 u_normalMatrix;

    in highp vec4 a_vertex;
    in highp vec4 a_normal;
    in highp vec2 a_uvs;

    out highp vec3 v_vertex;
    out highp vec3 v_normal;
    out highp vec2 v_uvs;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;

        v_uvs = a_uvs;
    }

fragment41core =
    #version 410
    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor;
    uniform highp vec3 u_lightPosition;
    uniform highp vec3 u_viewPosition;
    uniform mediump float u_opacity;
    uniform sampler2D u_texture;

    in highp vec3 v_vertex;
    in highp vec3 v_normal;
    in highp vec2 v_uvs;
    out vec4 frag_color;

    void main()
    {
        mediump vec4 final_color = vec4(0.0);

        /* Ambient Component */
        final_color += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 light_dir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float n_dot_l = clamp(dot(normal, light_dir), 0.0, 1.0);
        final_color += (n_dot_l * u_diffuseColor);

        final_color.a = u_opacity;

        lowp vec4 texture = texture(u_texture, v_uvs);
        final_color = mix(final_color, texture, texture.a);

        frag_color = final_color;
    }

[defaults]
u_ambientColor = [0.3, 0.3, 0.3, 1.0]
u_diffuseColor = [1.0, 1.0, 1.0, 1.0]
u_opacity = 0.5
u_texture = 0

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix
u_normalMatrix = normal_matrix
u_lightPosition = light_0_position
u_viewPosition = camera_position

[attributes]
a_vertex = vertex
a_normal = normal
a_uvs = uv0
