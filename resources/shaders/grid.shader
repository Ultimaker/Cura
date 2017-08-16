[shaders]
vertex =
    uniform highp mat4 u_modelViewProjectionMatrix;

    attribute highp vec4 a_vertex;
    attribute lowp vec2 a_uvs;

    varying lowp vec2 v_uvs;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        v_uvs = a_uvs;
    }

fragment =
    uniform lowp vec4 u_buildplateColor;
    varying lowp vec2 v_uvs;

    void main()
    {
        gl_FragColor = u_buildplateColor;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelViewProjectionMatrix;

    in highp vec4 a_vertex;
    in lowp vec2 a_uvs;

    out lowp vec2 v_uvs;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        v_uvs = a_uvs;
    }

fragment41core =
    #version 410
    uniform lowp vec4 u_buildplateColor;
    in lowp vec2 v_uvs;
    out vec4 frag_color;

    void main()
    {
        gl_FragColor = u_buildplateColor;
    }

[defaults]
u_buildplateColor = [0.96, 0.96, 0.96, 1.0]

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix

[attributes]
a_vertex = vertex
a_uvs = uv0
