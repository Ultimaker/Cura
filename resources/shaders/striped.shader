[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform highp mat4 u_normalMatrix;

    attribute highp vec4 a_vertex;
    attribute highp vec4 a_normal;
    attribute highp vec2 a_uvs;

    varying highp vec3 v_position;
    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_position = gl_Position.xyz;
        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;
    }

fragment =
    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor1;
    uniform mediump vec4 u_diffuseColor2;
    uniform mediump vec4 u_specularColor;
    uniform mediump float u_opacity;
    uniform highp vec3 u_lightPosition;
    uniform mediump float u_shininess;
    uniform highp vec3 u_viewPosition;

    uniform mediump float u_width;
    uniform bool u_vertical_stripes;

    varying highp vec3 v_position;
    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;

    void main()
    {
        mediump vec4 finalColor = vec4(0.0);
        mediump vec4 diffuseColor = u_vertical_stripes ?
            (((mod(v_vertex.x, u_width) < (u_width / 2.)) ^^ (mod(v_vertex.z, u_width) < (u_width / 2.))) ? u_diffuseColor1 : u_diffuseColor2) :
            ((mod(((-v_vertex.x + v_vertex.y + v_vertex.z) * 4.), u_width) < (u_width / 2.)) ? u_diffuseColor1 : u_diffuseColor2);

        /* Ambient Component */
        finalColor += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 lightDir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float NdotL = clamp(abs(dot(normal, lightDir)), 0.0, 1.0);
        finalColor += (NdotL * diffuseColor);

        /* Specular Component */
        /* TODO: We should not do specularity for fragments facing away from the light.*/
        highp vec3 reflectedLight = reflect(-lightDir, normal);
        highp vec3 viewVector = normalize(u_viewPosition - v_vertex);
        highp float NdotR = clamp(dot(viewVector, reflectedLight), 0.0, 1.0);
        finalColor += pow(NdotR, u_shininess) * u_specularColor;
        if (v_vertex.y <= 0.0)
        {
            finalColor.rgb = vec3(1.0, 1.0, 1.0) - finalColor.rgb;
        }

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

    out highp vec3 v_position;
    out highp vec3 v_vertex;
    out highp vec3 v_normal;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_projectionMatrix * u_viewMatrix * world_space_vert;

        v_position = gl_Position.xyz;
        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;
    }

fragment41core =
    #version 410
    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor1;
    uniform mediump vec4 u_diffuseColor2;
    uniform mediump vec4 u_specularColor;
    uniform mediump float u_opacity;
    uniform highp vec3 u_lightPosition;
    uniform mediump float u_shininess;
    uniform highp vec3 u_viewPosition;

    uniform mediump float u_width;
    uniform mediump bool u_vertical_stripes;

    in highp vec3 v_position;
    in highp vec3 v_vertex;
    in highp vec3 v_normal;

    out vec4 frag_color;

    void main()
    {
        mediump vec4 finalColor = vec4(0.0);
        mediump vec4 diffuseColor = u_vertical_stripes ?
            (((mod(v_vertex.x, u_width) < (u_width / 2.)) ^^ (mod(v_vertex.z, u_width) < (u_width / 2.))) ? u_diffuseColor1 : u_diffuseColor2) :
            ((mod(((-v_vertex.x + v_vertex.y + v_vertex.z) * 4.), u_width) < (u_width / 2.)) ? u_diffuseColor1 : u_diffuseColor2);

        /* Ambient Component */
        finalColor += u_ambientColor;

        highp vec3 normal = normalize(v_normal);
        highp vec3 lightDir = normalize(u_lightPosition - v_vertex);

        /* Diffuse Component */
        highp float NdotL = clamp(abs(dot(normal, lightDir)), 0.0, 1.0);
        finalColor += (NdotL * diffuseColor);

        /* Specular Component */
        /* TODO: We should not do specularity for fragments facing away from the light.*/
        highp vec3 reflectedLight = reflect(-lightDir, normal);
        highp vec3 viewVector = normalize(u_viewPosition - v_vertex);
        highp float NdotR = clamp(dot(viewVector, reflectedLight), 0.0, 1.0);
        finalColor += pow(NdotR, u_shininess) * u_specularColor;

        frag_color = finalColor;
        if (v_vertex.y <= 0.0)
        {
            frag_color.rgb = vec3(1.0, 1.0, 1.0) - frag_color.rgb;
        }
        frag_color.a = u_opacity;
    }

[defaults]
u_ambientColor = [0.3, 0.3, 0.3, 1.0]
u_diffuseColor1 = [1.0, 0.5, 0.5, 1.0]
u_diffuseColor2 = [0.5, 0.5, 0.5, 1.0]
u_specularColor = [0.4, 0.4, 0.4, 1.0]
u_opacity = 1.0
u_shininess = 20.0
u_width = 5.0
u_vertical_stripes = 0

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix
u_normalMatrix = normal_matrix
u_viewPosition = view_position
u_lightPosition = light_0_position
u_diffuseColor1 = diffuse_color
u_diffuseColor2 = diffuse_color_2

[attributes]
a_vertex = vertex
a_normal = normal
