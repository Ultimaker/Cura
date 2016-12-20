[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewProjectionMatrix;
    uniform highp mat4 u_modelViewProjectionMatrix;
    uniform lowp float u_active_extruder;
    uniform lowp float u_shade_factor;
    uniform highp mat4 u_normalMatrix;

    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;
    attribute highp vec4 a_normal;

    varying lowp vec4 v_color;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;

    varying highp vec3 v_orig_vertex;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        gl_Position = u_viewProjectionMatrix * world_space_vert;
        // gl_Position = u_modelViewProjectionMatrix * a_vertex;
        // shade the color depending on the extruder index stored in the alpha component of the color
        v_color = (a_color.a == u_active_extruder) ? a_color : a_color * u_shade_factor;
        v_color.a = 1.0;

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;

        v_orig_vertex = a_vertex.xyz;
    }

geometry =
    #version 410

    layout(lines) in;
    layout(triangle_strip, max_vertices = 6) out;

    in vec4 v_color[];
    in vec3 v_vertex[];
    in vec3 v_normal[];
    in vec3 v_orig_vertex[];

    out vec4 f_color;
    out vec3 f_normal;
    out vec3 f_vertex;

    void main()
    {
        int i;
        vec4 delta;
        vec3 g_normal;
        vec3 g_offset;

        vec3 g_vertex_delta;
        vec3 g_vertex_normal;

        float size = 3;

        /*
        delta = vec4(gl_in[1].gl_Position.xy, 0.0, 0.0) - vec4(gl_in[0].gl_Position.xy, 0.0, 0.0);

        if (length(delta) > 0.1) {
            g_normal = normalize(vec3(delta.y, -delta.x, delta.z));
            g_offset = vec3(g_normal.xy, 0); //5.0 * g_normal;  // vec3(3.5, 3.5, 0.0);
        } else {
            g_normal = vec3(delta.y, -delta.x, delta.z);
            g_offset = vec3(0.0, 0.0, 0.0);
        }
        g_offset = vec3(3.5, 3.5, 0.0); //5.0 * g_normal;  // vec3(3.5, 3.5, 0.0);
        */
        //g_normal = normalize(vec3(delta.y, -delta.x, delta.z));

        g_vertex_delta = v_orig_vertex[1] - v_orig_vertex[0];
        g_vertex_normal = vec3(g_vertex_delta.z, 0.0, -g_vertex_delta.x);
        if (length(g_vertex_normal) < 0.1) {
            g_vertex_normal = vec3(1.0, 0.0, 0.0);
        } else {
            g_vertex_normal = normalize(g_vertex_normal);
        }

        f_vertex = v_vertex[0];
        f_color = v_color[0];

        f_normal = g_vertex_normal;
        gl_Position = gl_in[0].gl_Position + vec4(0.0, size, 0.0, 0.0);
        EmitVertex();

        f_normal = g_vertex_normal;
        gl_Position = gl_in[1].gl_Position + vec4(0.0, size, 0.0, 0.0);
        EmitVertex();

        f_normal = vec3(0.0);
        gl_Position = gl_in[0].gl_Position + vec4(-size, 0.0, 0.0, 0.0);
        EmitVertex();

        //f_vertex = v_vertex[1];
        //f_color = v_color[1];


        f_normal = vec3(0.0);
        gl_Position = gl_in[1].gl_Position + vec4(size, 0.0, 0.0, 0.0);
        EmitVertex();

        f_normal = -g_vertex_normal;
        gl_Position = gl_in[0].gl_Position + vec4(0, -size, 0.0, 0.0);
        EmitVertex();

        f_normal = -g_vertex_normal;
        gl_Position = gl_in[1].gl_Position + vec4(0.0, -size, 0.0, 0.0);
        EmitVertex();

        EndPrimitive();

        /*
        f_vertex = v_vertex[0];
        f_normal = -g_vertex_normal;
        f_color = v_color[0];
        gl_Position = gl_in[0].gl_Position - g_offset;
        EmitVertex();

        f_vertex = v_vertex[1];
        f_normal = g_vertex_normal;
        f_color = v_color[1];
        gl_Position = gl_in[1].gl_Position + g_offset;
        EmitVertex();

        f_vertex = v_vertex[1];
        f_normal = -g_vertex_normal;
        f_color = v_color[1];
        gl_Position = gl_in[1].gl_Position - g_offset;
        EmitVertex();
        */


    }

fragment =
    varying lowp vec4 f_color;
    varying lowp vec3 f_normal;
    varying lowp vec3 f_vertex;

    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_diffuseColor;
    uniform highp vec3 u_lightPosition;

    void Impostor(in float sphereRadius, in vec3 cameraSpherePos, in vec2 mapping, out vec3 cameraPos, out vec3 cameraNormal)
    {
        float lensqr = dot(mapping, mapping);
        if(lensqr > 1.0)
            discard;

        cameraNormal = vec3(mapping, sqrt(1.0 - lensqr));
        cameraPos = (cameraNormal * sphereRadius) + cameraSpherePos;
    }

    void main()
    {
        vec3 cameraPos;
        vec3 cameraNormal;

        Impostor(0.2, vec3(0.0, 0.0, 0.0), vec2(0.1, 0.0), cameraPos, cameraNormal);

        mediump vec4 finalColor = vec4(0.0);

        finalColor += u_ambientColor;

        //highp vec3 normal = normalize(f_normal);
        highp vec3 normal = normalize(cameraNormal);
        highp vec3 lightDir = normalize(u_lightPosition - f_vertex);

        // Diffuse Component
        highp float NdotL = clamp(dot(normal, lightDir), 0.0, 1.0);
        finalColor += (NdotL * f_color);

        finalColor.a = 1.0;
        gl_FragColor = finalColor;

        //gl_FragColor = f_color;
        //gl_FragColor = vec4(f_normal, 1.0);
    }

[defaults]
u_active_extruder = 0.0
u_shade_factor = 0.60
u_ambientColor = [0.3, 0.3, 0.3, 0.3]
u_diffuseColor = [1.0, 0.79, 0.14, 1.0]

[bindings]
u_modelViewProjectionMatrix = model_view_projection_matrix
u_modelMatrix = model_matrix
u_viewProjectionMatrix = view_projection_matrix
u_normalMatrix = normal_matrix
u_lightPosition = light_0_position

[attributes]
a_vertex = vertex
a_color = color
a_normal = normal