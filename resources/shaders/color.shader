[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    attribute highp vec4 a_vertex; //Vertex coordinate.
    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex; //Transform the vertex coordinates with the model view projection.
    }

fragment =
    uniform lowp vec4 u_color;

    void main()
    {
        gl_FragColor = u_color; //Always use the uniform colour. The entire mesh will be the same colour.
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    in highp vec4 a_vertex; //Vertex coordinate.
    void main()
    {
        gl_Position = u_projectionMatrix * u_viewMatrix * u_modelMatrix * a_vertex; //Transform the vertex coordinates with the model view projection.
    }

fragment41core =
    #version 410
    uniform lowp vec4 u_color;
    uniform lowp float u_z_bias; //Bias in the depth buffer for rendering this object (to make an object be rendered in front of or behind other objects).

    out vec4 frag_color;

    void main()
    {
        frag_color = u_color; //Always use the uniform colour. The entire mesh will be the same colour.*/
        gl_FragDepth = gl_FragCoord.z + u_z_bias;
    }

[defaults]
u_color = [0.5, 0.5, 0.5, 1.0]
u_z_bias = 0.0

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix

[attributes]
a_vertex = vertex
