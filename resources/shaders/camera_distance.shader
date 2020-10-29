[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    attribute highp vec4 a_vertex;

    varying highp vec3 v_vertex;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_vertex = world_space_vert.xyz;
    }

fragment =
    uniform highp vec3 u_viewPosition;

    varying highp vec3 v_vertex;

    void main()
    {
        highp float distance_to_camera = distance(v_vertex, u_viewPosition) * 1000.; // distance in micron

        vec3 encoded; // encode float into 3 8-bit channels; this gives a precision of a micron at a range of up to ~16 meter
        encoded.r = floor(distance_to_camera / 65536.0);
        encoded.g = floor((distance_to_camera - encoded.r * 65536.0) / 256.0);
        encoded.b = floor(distance_to_camera - encoded.r * 65536.0 - encoded.g * 256.0);

        gl_FragColor.rgb = encoded / 255.;
        gl_FragColor.a = 1.0;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    in highp vec4 a_vertex;

    out highp vec3 v_vertex;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_vertex = world_space_vert.xyz;
    }

fragment41core =
    #version 410
    uniform highp vec3 u_viewPosition;

    in highp vec3 v_vertex;

    out vec4 frag_color;

    void main()
    {
        highp float distance_to_camera = distance(v_vertex, u_viewPosition) * 1000.; // distance in micron

        vec3 encoded; // encode float into 3 8-bit channels; this gives a precision of a micron at a range of up to ~16 meter
        encoded.r = floor(distance_to_camera / 65536.0);
        encoded.g = floor((distance_to_camera - encoded.r * 65536.0) / 256.0);
        encoded.b = floor(distance_to_camera - encoded.r * 65536.0 - encoded.g * 256.0);

        frag_color.rgb = encoded / 255.;
        frag_color.a = 1.0;
    }

[defaults]

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix
u_normalMatrix = normal_matrix
u_viewPosition = view_position

[attributes]
a_vertex = vertex
