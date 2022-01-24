[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    attribute highp vec4 a_vertex;
    attribute lowp vec2 a_uvs;

    varying lowp vec2 v_uvs;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        v_uvs = a_uvs;
    }

fragment =
    #ifdef GL_ES
        #extension GL_OES_standard_derivatives : enable
        #ifdef GL_FRAGMENT_PRECISION_HIGH
            precision highp float;
        #else
            precision mediump float;
        #endif // GL_FRAGMENT_PRECISION_HIGH
    #endif // GL_ES
    uniform lowp vec4 u_plateColor;
    uniform lowp vec4 u_gridColor0;
    uniform lowp vec4 u_gridColor1;

    varying lowp vec2 v_uvs;

    void main()
    {
        vec2 coord = v_uvs.xy;

        // Compute anti-aliased world-space minor grid lines
        vec2 minorGrid = abs(fract(coord - 0.5) - 0.5) / fwidth(coord);
        float minorLine = min(minorGrid.x, minorGrid.y);

        vec4 minorGridColor = mix(u_plateColor, u_gridColor1, 1.0 - min(minorLine, 1.0));

        // Compute anti-aliased world-space major grid lines
        vec2 majorGrid = abs(fract(coord / 10.0 - 0.5) - 0.5) / fwidth(coord / 10.0);
        float majorLine = min(majorGrid.x, majorGrid.y);

        gl_FragColor = mix(minorGridColor, u_gridColor0, 1.0 - min(majorLine, 1.0));
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    in highp vec4 a_vertex;
    in lowp vec2 a_uvs;

    out lowp vec2 v_uvs;

    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex;
        v_uvs = a_uvs;
    }

fragment41core =
    #version 410
    uniform lowp vec4 u_plateColor;
    uniform lowp vec4 u_gridColor0;
    uniform lowp vec4 u_gridColor1;

    in lowp vec2 v_uvs;
    out vec4 frag_color;

    void main()
    {
        vec2 coord = v_uvs.xy;

        // Compute anti-aliased world-space minor grid lines
        vec2 minorGrid = abs(fract(coord - 0.5) - 0.5) / fwidth(coord);
        float minorLine = min(minorGrid.x, minorGrid.y);

        vec4 minorGridColor = mix(u_plateColor, u_gridColor1, 1.0 - min(minorLine, 1.0));

        // Compute anti-aliased world-space major grid lines
        vec2 majorGrid = abs(fract(coord / 10.0 - 0.5) - 0.5) / fwidth(coord / 10.0);
        float majorLine = min(majorGrid.x, majorGrid.y);

        frag_color = mix(minorGridColor, u_gridColor0, 1.0 - min(majorLine, 1.0));
    }

[defaults]
u_plateColor = [1.0, 1.0, 1.0, 1.0]
u_gridColor0 = [0.96, 0.96, 0.96, 1.0]
u_gridColor1 = [0.8, 0.8, 0.8, 1.0]

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix

[attributes]
a_vertex = vertex
a_uvs = uv0
