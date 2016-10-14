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
    uniform lowp vec4 u_gridColor0;
    uniform lowp vec4 u_gridColor1;

    varying lowp vec2 v_uvs;

    void main()
    {
        if (mod(floor(v_uvs.x / 10.0) - floor(v_uvs.y / 10.0), 2.0) < 1.0)
            gl_FragColor = u_gridColor0;
        else
            gl_FragColor = u_gridColor1;
    }

[defaults]
u_gridColor0 = [0.96, 0.96, 0.96, 1.0]
u_gridColor1 = [0.8, 0.8, 0.8, 1.0]

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix

[attributes]
a_vertex = vertex
a_uvs = uv0
