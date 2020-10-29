[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    attribute highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
    }

fragment =
    void main()
    {
        gl_FragColor = vec4(0., 0., 0., 1.);
        // NOTE: Select face can't be used in compatibility-mode;
        //       the __VERSION__ macro may give back the max the graphics driver supports,
        //       rather than the one supported by the selected OpenGL version.
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    in highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
    }

fragment41core =
    #version 410
    out vec4 frag_color;

    void main()
    {
        frag_color = vec4(0., 0., 0., 1.);
        frag_color.r = (gl_PrimitiveID % 0x100) / 255.;
        frag_color.g = ((gl_PrimitiveID / 0x100) % 0x100) / 255.;
        frag_color.b = (0x1 + 2 * ((gl_PrimitiveID / 0x10000) % 0x80)) / 255.;
        // Don't use alpha for anything, as some faces may be behind others, an only the front one's value is desired.
        // There isn't any control over the background color, so a signal-bit is put into the blue byte.
    }

[defaults]

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix

[attributes]
a_vertex = vertex
