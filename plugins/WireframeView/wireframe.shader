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
    uniform lowp vec4 u_color_overhang;

    layout(triangles) in;
    layout(line_strip, max_vertices = 6) out;

    in highp vec3 face_normal[];

    out lowp vec4 edge_color;

    void makeEdge(vec4 from, vec4 to)
    {
        gl_Position = from;
        EmitVertex();
        gl_Position = to;
        EmitVertex();
    }
    
    void main()
    {
        vec3 edge_normal = normalize(face_normal[0]);
        edge_color = (-edge_normal.y > u_overhang_angle)? u_color_overhang : u_color;
        makeEdge(gl_in[0].gl_Position, gl_in[1].gl_Position);
        makeEdge(gl_in[1].gl_Position, gl_in[2].gl_Position);
        makeEdge(gl_in[2].gl_Position, gl_in[0].gl_Position);
        EndPrimitive();
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
u_color_overhang = [1.0, 0.0, 0.0, 1.0]

[bindings]
u_model_view_projection_matrix = model_view_projection_matrix
u_normalMatrix = normal_matrix

[attributes]
a_vertex = vertex
a_normal = normal
