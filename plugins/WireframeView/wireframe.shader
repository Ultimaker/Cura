[shaders]
vertex =
    uniform highp mat4 u_modelViewProjectionMatrix;

    attribute highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
    }

fragment =
    uniform lowp vec4 u_color;

    void main()
    {
        gl_FragColor = u_color;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelViewProjectionMatrix;

    in highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
    }


geometry41core =
    #version 410

    uniform highp mat4 u_modelViewProjectionMatrix;

    layout(triangles) in;
    layout(line_strip, max_vertices = 4) out;

    void main()
    {
        gl_Position = gl_in[0].gl_Position;
        EmitVertex();
        gl_Position = gl_in[1].gl_Position;
        EmitVertex();
        gl_Position = gl_in[2].gl_Position;
        EmitVertex();
        gl_Position = gl_in[0].gl_Position;
        EmitVertex();
        EndPrimitive();
    }

fragment41core =
    #version 410
    uniform lowp vec4 u_color;

    out vec4 frag_color;

    void main()
    {
        frag_color = u_color;
    }

[defaults]
u_color = [0.02, 0.02, 0.02, 1.0]

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix

[attributes]
a_vertex = vertex
