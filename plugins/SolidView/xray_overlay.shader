[shaders]
vertex =
    uniform highp mat4 u_modelViewProjectionMatrix;

    attribute highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
    }

fragment =
    uniform lowp vec4 u_xray_error;

    void main()
    {
        gl_FragColor = u_xray_error;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelViewProjectionMatrix;

    in highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
    }

fragment41core =
    #version 410
    uniform lowp vec4 u_xray_error;

    out vec4 frag_color;

    void main()
    {

        frag_color = u_xray_error;
    }

[defaults]
u_xray_error = [1.0, 1.0, 1.0, 1.0]

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix

[attributes]
a_vertex = vertex
