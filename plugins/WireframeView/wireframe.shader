[shaders]
vertex =
    uniform highp mat4 u_model_view_projection_matrix;

    attribute highp vec4 a_vertex;

    void main()
    {
        gl_Position = u_model_view_projection_matrix * a_vertex;
    }

fragment =
    uniform lowp vec4 u_color;

    void main()
    {
        gl_FragColor = u_color;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_model_view_projection_matrix;
    uniform highp mat4 u_normalMatrix;

    in highp vec4 a_vertex;
    in highp vec4 a_normal;

    out highp vec3 face_normal;

    void main()
    {
        gl_Position = u_model_view_projection_matrix * a_vertex;
        face_normal = (u_normalMatrix * normalize(a_normal)).xyz;
    }


geometry41core =
    #version 410

    uniform highp mat4 u_model_view_projection_matrix;
    uniform lowp float u_overhang_angle;
    uniform lowp vec4 u_color;
    uniform lowp vec4 u_color_error;

    layout(triangles_adjacency) in;
    layout(line_strip, max_vertices = 12) out;

    in highp vec3 face_normal[];

    out lowp vec4 edge_color;

    void makeEdge(vec4 from, vec4 to, vec3 n1, vec3 n2)
    {
        vec3 edge_normal = normalize(n1 + n2);
        edge_color = (-edge_normal.y > u_overhang_angle)? u_color_error : u_color;
        gl_Position = from;
        EmitVertex();
        gl_Position = to;
        EmitVertex();
        EndPrimitive();
    }
    
    void main()
    {
        makeEdge(gl_in[0].gl_Position, gl_in[2].gl_Position, face_normal[0], face_normal[1]);
        makeEdge(gl_in[2].gl_Position, gl_in[4].gl_Position, face_normal[0], face_normal[2]);
        makeEdge(gl_in[4].gl_Position, gl_in[0].gl_Position, face_normal[0], face_normal[3]);
    }

fragment41core =
    #version 410

    in lowp vec4 edge_color;
    out vec4 frag_color;

    void main()
    {
        frag_color = edge_color;
    }

[defaults]
u_color = [0.02, 0.02, 0.02, 1.0]
u_color_error = [1.0, 0.0, 0.0, 1.0]

[bindings]
u_model_view_projection_matrix = model_view_projection_matrix
u_normalMatrix = normal_matrix

[attributes]
a_vertex = vertex
a_normal = normal
