[shaders]
vertex =
    uniform highp mat4 u_modelViewProjectionMatrix;
    uniform lowp float u_active_extruder;
    uniform lowp float u_shade_factor;

    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;
    varying lowp vec4 v_color;
    void main()
    {
        gl_Position = u_modelViewProjectionMatrix * a_vertex;
        // shade the color depending on the extruder index stored in the alpha component of the color
        v_color = (a_color.a == u_active_extruder) ? a_color : a_color * u_shade_factor;
        v_color.a = 1.0;
    }

fragment =
    varying lowp vec4 v_color;

    void main()
    {
        gl_FragColor = v_color;
    }

[defaults]
u_active_extruder = 0.0
u_shade_factor = 0.75

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix

[attributes]
a_vertex = vertex
a_color = color
