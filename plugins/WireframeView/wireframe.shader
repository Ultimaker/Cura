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
    uniform highp mat4 u_normalMatrix;

    in highp vec4 a_vertex;
    in highp vec4 a_normal;

    out highp vec3 f_normal;

    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        f_normal = (u_normalMatrix * normalize(a_normal)).xyz;
    }


geometry41core =
    #version 410

    uniform highp mat4 u_modelViewProjectionMatrix;
    uniform lowp float u_overhangAngle;
    uniform lowp vec4 u_color;
    uniform lowp vec4 u_color_error;

    layout(triangles_adjacency) in;
    layout(line_strip, max_vertices = 12) out;

    in highp vec3 f_normal[];

    out lowp vec4 e_color;

    void makeEdge(vec4 from, vec4 to, vec3 n1, vec3 n2)
    {
        vec3 edge_normal = normalize(n1 + n2);
        e_color = (-edge_normal.y > u_overhangAngle)? u_color_error : u_color;
        gl_Position = from;
        EmitVertex();
        gl_Position = to;
        EmitVertex();
        EndPrimitive();
    }
    
    void main()
    {
        makeEdge(gl_in[0].gl_Position, gl_in[2].gl_Position, f_normal[0], f_normal[1]);
        makeEdge(gl_in[2].gl_Position, gl_in[4].gl_Position, f_normal[0], f_normal[2]);
        makeEdge(gl_in[4].gl_Position, gl_in[0].gl_Position, f_normal[0], f_normal[3]);
    }

fragment41core =
    #version 410

    in lowp vec4 e_color;
    out vec4 frag_color;

    void main()
    {
        frag_color = e_color;
    }

[defaults]
u_color = [0.02, 0.02, 0.02, 1.0]
u_color_error = [1.0, 0.0, 0.0, 1.0]

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix
u_normalMatrix = normal_matrix

[attributes]
a_vertex = vertex
a_normal = normal
