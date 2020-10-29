[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;

    varying lowp vec4 v_color;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        v_color = a_color;
    }

fragment =
    uniform lowp vec4 u_disabledColor;
    uniform lowp vec4 u_activeColor;
    uniform lowp float u_disabledMultiplier;

    varying lowp vec4 v_color;

    void main()
    {
        if(u_activeColor == v_color)
        {
            gl_FragColor = v_color;
        }
        else
        {
            gl_FragColor = v_color * u_disabledMultiplier;
        }
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    in highp vec4 a_vertex;
    in lowp vec4 a_color;

    out lowp vec4 v_color;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        v_color = a_color;
    }

fragment41core =
    #version 410
    uniform lowp vec4 u_disabledColor;
    uniform lowp vec4 u_activeColor;
    uniform lowp float u_disabledMultiplier;

    in lowp vec4 v_color;
    out vec4 frag_color;

    void main()
    {
        if(u_activeColor == v_color)
        {
            frag_color = v_color;
        }
        else
        {
            frag_color = v_color * u_disabledMultiplier;
        }
    }

[defaults]
u_disabledColor = [0.5, 0.5, 0.5, 1.0]
u_activeColor = [0.5, 0.5, 0.5, 1.0]
u_disabledMultiplier = 0.75

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix

[attributes]
a_vertex = vertex
a_color = color
