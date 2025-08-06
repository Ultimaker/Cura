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
    uniform highp vec3 u_lightPosition;
    uniform highp vec3 u_viewPosition;
    uniform sampler2D u_texture;
    uniform mediump int u_bitsRangesStart;
    uniform mediump int u_bitsRangesEnd;
    uniform mediump vec3 u_renderColors[16];

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
        ivec4 texture = ivec4(texture(u_texture, v_uvs) * 255.0);
        uint color_index = (texture.r << 16) | (texture.g << 8) | texture.b;
        color_index = (color_index << (32 - 1 - u_bitsRangesEnd)) >> 32 - 1 - (u_bitsRangesEnd - u_bitsRangesStart);

        vec4 diffuse_color = vec4(u_renderColors[color_index] / 255.0, 1.0);
        highp float n_dot_l = mix(0.3, 0.7, dot(normal, light_dir));
        final_color += (n_dot_l * diffuse_color);

        final_color.a = 1.0;

        frag_color = final_color;
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
    uniform highp vec3 u_lightPosition;
    uniform highp vec3 u_viewPosition;
    uniform sampler2D u_texture;
    uniform mediump int u_bitsRangesStart;
    uniform mediump int u_bitsRangesEnd;
    uniform mediump vec3 u_renderColors[16];

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
        ivec4 texture = ivec4(texture(u_texture, v_uvs) * 255.0);
        uint color_index = (texture.r << 16) | (texture.g << 8) | texture.b;
        color_index = (color_index << (32 - 1 - u_bitsRangesEnd)) >> 32 - 1 - (u_bitsRangesEnd - u_bitsRangesStart);

        vec4 diffuse_color = vec4(u_renderColors[color_index] / 255.0, 1.0);
        highp float n_dot_l = mix(0.3, 0.7, dot(normal, light_dir));
        final_color += (n_dot_l * diffuse_color);

        final_color.a = 1.0;

        frag_color = final_color;
    }

[defaults]
u_ambientColor = [0.3, 0.3, 0.3, 1.0]
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
