[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform highp mat4 u_normalMatrix;

    attribute highp vec4 a_vertex;
    attribute highp vec4 a_normal;
    attribute highp vec2 a_uvs;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;
    }

fragment =
    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor;
    uniform highp vec3 u_lightPosition;

    uniform mediump float u_opacity;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;

    void main()
    {
        mediump vec4 finalColor = vec4(0.0);

        /* Ambient Component */
        finalColor += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 lightDir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float NdotL = clamp(abs(dot(normal, lightDir)), 0.0, 1.0);
        finalColor += (NdotL * u_diffuseColor);

        gl_FragColor = finalColor;
        gl_FragColor.a = u_opacity;
    }

vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform highp mat4 u_normalMatrix;

    in highp vec4 a_vertex;
    in highp vec4 a_normal;
    in highp vec2 a_uvs;

    out highp vec3 v_vertex;
    out highp vec3 v_normal;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;
    }

fragment41core =
    #version 410
    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor;
    uniform highp vec3 u_lightPosition;

    uniform mediump float u_opacity;

    in highp vec3 v_vertex;
    in highp vec3 v_normal;

    out vec4 frag_color;

    void main()
    {
        mediump vec4 finalColor = vec4(0.0);

        /* Ambient Component */
        finalColor += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 lightDir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float NdotL = clamp(abs(dot(normal, lightDir)), 0.0, 1.0);
        finalColor += (NdotL * u_diffuseColor);

        frag_color = finalColor;
        frag_color.a = u_opacity;
    }

[defaults]
u_ambientColor = [0.1, 0.1, 0.1, 1.0]
u_diffuseColor = [0.4, 0.4, 0.4, 1.0]
u_opacity = 0.5

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix
u_normalMatrix = normal_matrix
u_lightPosition = light_0_position
u_diffuseColor = diffuse_color

[attributes]
a_vertex = vertex
a_normal = normal
