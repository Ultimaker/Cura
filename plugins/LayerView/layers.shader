[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    //uniform highp mat4 u_viewProjectionMatrix;
    //uniform highp mat4 u_modelViewProjectionMatrix;
    uniform lowp float u_active_extruder;
    uniform lowp float u_shade_factor;
    uniform highp mat4 u_normalMatrix;

    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;
    attribute highp vec4 a_normal;

    varying lowp vec4 v_color;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;

    varying highp vec4 v_orig_vertex;

    varying lowp vec4 f_color;
    varying highp vec3 f_vertex;
    varying highp vec3 f_normal;

    void main()
    {
        vec4 world_space_vert = u_modelMatrix * a_vertex;
        // gl_Position = u_viewProjectionMatrix * world_space_vert;
        gl_Position = world_space_vert;
        // gl_Position = u_modelViewProjectionMatrix * a_vertex;
        // shade the color depending on the extruder index stored in the alpha component of the color
        v_color = (a_color.a == u_active_extruder) ? a_color : a_color * u_shade_factor;
        v_color.a = 1.0;

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;

        v_orig_vertex = a_vertex;

        // for testing without geometry shader
        f_color = v_color;
        f_vertex = v_vertex;
        f_normal = v_normal;
    }

geometry =
    #version 410

    //uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewProjectionMatrix;
    //uniform highp mat4 u_modelViewProjectionMatrix;

    layout(lines) in;
    layout(triangle_strip, max_vertices = 4) out;
    /*layout(std140) uniform Matrices {
        mat4 u_modelViewProjectionMatrix;
    };*/

    in vec4 v_color[];
    in vec3 v_vertex[];
    in vec3 v_normal[];
    in vec3 v_orig_vertex[];

    out vec4 f_color;
    out vec3 f_normal;
    out vec3 f_vertex;

    void main()
    {
        //int i;
        //vec3 g_normal;
        //vec3 g_offset;

        //vec4 g_vertex_delta;
        vec3 g_vertex_normal_horz;  // horizontal and vertical in respect to layers
        vec3 g_vertex_normal_vert;
        vec3 g_vertex_offset_horz;
        vec3 g_vertex_offset_vert;

        float size = 0.5;

        //g_vertex_delta = gl_in[1].gl_Position - gl_in[0].gl_Position;
        g_vertex_normal_horz = normalize(v_normal[0]);  //vec3(g_vertex_delta.z, g_vertex_delta.y, -g_vertex_delta.x);
        g_vertex_offset_horz = vec3(0.5, 0.0, 0.0); //size * g_vertex_normal_horz; //size * g_vertex_normal_horz;
        g_vertex_normal_vert = vec3(0.0, 1.0, 0.0);
        g_vertex_offset_vert = vec3(0.0, 0.5, 0.0);  //size * g_vertex_normal_vert;

        f_vertex = v_vertex[0];
        f_normal = g_vertex_normal_horz;
        f_color = vec4(g_vertex_normal_horz, 1.0); //v_color[0];
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[1];
        //f_color = v_color[1];
        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[0];
        //f_color = v_color[0];
        f_normal = g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_vert);
        EmitVertex();

        f_vertex = v_vertex[1];
        //f_color = v_color[1];
        f_normal = g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_vert);
        EmitVertex();

        EndPrimitive();
    }


poep =
    #version 410

    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewProjectionMatrix;
    uniform highp mat4 u_modelViewProjectionMatrix;

    layout(lines) in;
    layout(triangle_strip, max_vertices = 3) out;

    in vec4 v_color[];
    in vec3 v_vertex[];
    in vec3 v_normal[];
    in vec4 v_orig_vertex[];

    out vec4 f_color;
    out vec3 f_normal;
    out vec3 f_vertex;

    void main()
    {
        int i;
        vec4 delta;
        vec3 g_normal;
        vec3 g_offset;

        vec4 g_vertex_delta;
        vec4 g_vertex_normal_horz;  // horizontal and vertical in respect to layers
        vec3 g_vertex_normal_vert;
        vec3 g_vertex_offset_horz;
        vec3 g_vertex_offset_vert;

        float size = 3;

        g_vertex_delta = v_orig_vertex[1] - v_orig_vertex[0];
        g_vertex_normal_horz = vec4(g_vertex_delta.z, 0.0, -g_vertex_delta.x, g_vertex_delta.w);
        if (length(g_vertex_normal_horz) < 0.1) {
            g_vertex_normal_horz = vec4(1.0, 0.0, 0.0, 0.0);
            g_vertex_offset_horz = vec3(0.0, 0.0, 0.0);
            g_vertex_offset_vert = vec3(0.0, 0.0, 0.0);
        } else {
            g_vertex_normal_horz = normalize(g_vertex_normal_horz);
            g_vertex_offset_horz = (u_viewProjectionMatrix * u_modelMatrix * size * g_vertex_normal_horz).xyz;
            g_vertex_normal_vert = vec3(0.0, 0.0, 1.0);
            g_vertex_offset_vert = (u_viewProjectionMatrix * u_modelMatrix * size * g_vertex_normal_vert).xyz;
        }

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = g_vertex_normal_horz;
        gl_Position = gl_in[0].gl_Position + g_vertex_offset_horz;
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = g_vertex_normal_horz;
        gl_Position = gl_in[1].gl_Position + g_vertex_offset_horz;
        EmitVertex();

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = g_vertex_offset_vert;
        gl_Position = gl_in[0].gl_Position + g_vertex_offset_vert;
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = g_vertex_offset_vert;
        gl_Position = gl_in[1].gl_Position + g_vertex_offset_vert;
        EmitVertex();

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = -g_vertex_normal_horz;
        gl_Position = gl_in[0].gl_Position - g_vertex_offset_horz;
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = -g_vertex_normal_horz;
        gl_Position = gl_in[1].gl_Position - g_vertex_offset_horz;
        EmitVertex();

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = -g_vertex_offset_vert;
        gl_Position = gl_in[0].gl_Position - g_vertex_offset_vert;
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = -g_vertex_offset_vert;
        gl_Position = gl_in[1].gl_Position - g_vertex_offset_vert;
        EmitVertex();


        EndPrimitive();



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

        //Impostor(0.2, vec3(0.0, 0.0, 0.0), vec2(0.1, 0.1), cameraPos, cameraNormal);

        mediump vec4 finalColor = vec4(0.0);

        //finalColor += u_ambientColor;
        finalColor = f_color;

        highp vec3 normal = normalize(f_normal);
        //highp vec3 normal = normalize(cameraNormal);
        highp vec3 lightDir = normalize(u_lightPosition - f_vertex);

        // Diffuse Component
        highp float NdotL = clamp(dot(normal, lightDir), 0.0, 1.0);
        //finalColor += (NdotL * f_color);

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