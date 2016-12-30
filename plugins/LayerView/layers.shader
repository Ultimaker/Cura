[shaders]
vertex =
    uniform highp mat4 u_modelMatrix;
    //uniform highp mat4 u_viewProjectionMatrix;
    //uniform highp mat4 u_modelViewProjectionMatrix;
    uniform lowp float u_active_extruder;
    uniform lowp int u_layer_view_type;
    uniform lowp int u_only_color_active_extruder;
    uniform lowp vec4 u_extruder_opacity;  // currently only for max 4 extruders, others always visible

    uniform highp mat4 u_normalMatrix;

    attribute highp vec4 a_vertex;
    attribute lowp vec4 a_color;
    attribute lowp vec4 a_material_color;
    attribute highp vec4 a_normal;
    attribute highp vec2 a_line_dim;  // line width and thickness
    attribute highp int a_extruder;
    attribute highp int a_line_type;

    varying lowp vec4 v_color;
    //varying lowp vec4 v_material_color;

    varying highp vec3 v_vertex;
    varying highp vec3 v_normal;
    //varying lowp vec2 v_uvs;
    varying lowp vec2 v_line_dim;
    varying highp int v_extruder;
    varying highp vec4 v_extruder_opacity;
    varying int v_line_type;

    varying lowp vec4 f_color;
    varying highp vec3 f_vertex;
    varying highp vec3 f_normal;
    varying highp int f_extruder;

    void main()
    {
        vec4 v1_vertex = a_vertex;
        v1_vertex.y -= a_line_dim.y / 2;  // half layer down
        vec4 world_space_vert = u_modelMatrix * v1_vertex;
        // gl_Position = u_viewProjectionMatrix * world_space_vert;
        gl_Position = world_space_vert;
        // gl_Position = u_modelViewProjectionMatrix * a_vertex;
        // shade the color depending on the extruder index stored in the alpha component of the color

        switch (u_layer_view_type) {
            case 0:  // "Material color"
                v_color = a_material_color;
                break;
            case 1:  // "Line type"
                v_color = a_color;
                break;
        }
        if ((u_only_color_active_extruder == 1) && (a_line_type != 8) && (a_line_type != 9)) {
            v_color = (a_extruder == u_active_extruder) ? v_color : vec4(0.4, 0.4, 0.4, v_color.a);
        }
        /*if (a_extruder < 4) {
            v_color.a *= u_extruder_opacity[a_extruder];  // make it (in)visible
        }*/

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;
        v_line_dim = a_line_dim;
        v_extruder = a_extruder;
        v_line_type = a_line_type;
        v_extruder_opacity = u_extruder_opacity;

        // for testing without geometry shader
        /*f_color = v_color;
        f_vertex = v_vertex;
        f_normal = v_normal;
        f_extruder = v_extruder; */
    }

geometry =
    #version 410

    uniform highp mat4 u_viewProjectionMatrix;
    uniform int u_show_travel_moves;
    uniform int u_show_support;
    uniform int u_show_adhesion;
    uniform int u_show_skin;
    uniform int u_show_infill;

    layout(lines) in;
    layout(triangle_strip, max_vertices = 26) out;

    in vec4 v_color[];
    in vec3 v_vertex[];
    in vec3 v_normal[];
    in vec2 v_line_dim[];
    in int v_extruder[];
    in vec4 v_extruder_opacity[];
    in int v_line_type[];

    out vec4 f_color;
    out vec3 f_normal;
    out vec3 f_vertex;
    out uint f_extruder;
    //out vec4 f_material_color;

    void main()
    {
        vec4 g_vertex_delta;
        vec3 g_vertex_normal_horz;  // horizontal and vertical in respect to layers
        vec4 g_vertex_offset_horz;  // vec4 to match gl_in[x].gl_Position
        vec3 g_vertex_normal_vert;
        vec4 g_vertex_offset_vert;
        vec3 g_vertex_normal_horz_head;
        vec4 g_vertex_offset_horz_head;

        float size_x;
        float size_y;

        if ((v_extruder_opacity[0][v_extruder[0]] == 0.0) && (v_line_type[0] != 8) && (v_line_type[0] != 9)) {
            return;
        }
        // See LayerPolygon; 8 is MoveCombingType, 9 is RetractionType
        if ((u_show_travel_moves == 0) && ((v_line_type[0] == 8) || (v_line_type[0] == 9))) {
            return;
        }
        if ((u_show_support == 0) && ((v_line_type[0] == 4) || (v_line_type[0] == 7) || (v_line_type[0] == 10))) {
            return;
        }
        if ((u_show_adhesion == 0) && (v_line_type[0] == 5)) {
            return;
        }
        if ((u_show_skin == 0) && ((v_line_type[0] == 1) || (v_line_type[0] == 2) || (v_line_type[0] == 3))) {
            return;
        }
        if ((u_show_infill == 0) && (v_line_type[0] == 6)) {
            return;
        }

        if ((v_line_type[0] == 8) || (v_line_type[0] == 9)) {
            // fixed size for movements
            size_x = 0.1;
            size_y = 0.1;
        } else {
            size_x = v_line_dim[0].x / 2 + 0.01;  // radius, and make it nicely overlapping
            size_y = v_line_dim[0].y / 2 + 0.01;
        }

        f_extruder = v_extruder[0];

        g_vertex_delta = gl_in[1].gl_Position - gl_in[0].gl_Position;
        g_vertex_normal_horz_head = normalize(vec3(-g_vertex_delta.x, -g_vertex_delta.y, -g_vertex_delta.z));
        g_vertex_offset_horz_head = vec4(g_vertex_normal_horz_head * size_x, 0.0);

        g_vertex_normal_horz = normalize(vec3(g_vertex_delta.z, g_vertex_delta.y, -g_vertex_delta.x));

        g_vertex_offset_horz = vec4(g_vertex_normal_horz * size_x, 0.0); //size * g_vertex_normal_horz;
        g_vertex_normal_vert = vec3(0.0, 1.0, 0.0);
        g_vertex_offset_vert = vec4(g_vertex_normal_vert * size_y, 0.0);

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_vert);
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_vert);
        EmitVertex();

        f_vertex = v_vertex[0];
        f_normal = -g_vertex_normal_horz;
        f_color = v_color[0];
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = -g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[0];
        f_color = v_color[0];
        f_normal = -g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_vert);
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = -g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_vert);
        EmitVertex();

        f_vertex = v_vertex[0];
        f_normal = g_vertex_normal_horz;
        f_color = v_color[0];
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_vertex = v_vertex[1];
        f_color = v_color[1];
        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        EndPrimitive();

        // left side
        f_vertex = v_vertex[0];
        f_color = v_color[0];

        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_normal = g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_vert);
        EmitVertex();

        f_normal = g_vertex_normal_horz_head;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz_head);
        EmitVertex();

        f_normal = -g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_horz);
        EmitVertex();

        EndPrimitive();

        f_normal = -g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_horz);
        EmitVertex();

        f_normal = -g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_vert);
        EmitVertex();

        f_normal = g_vertex_normal_horz_head;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz_head);
        EmitVertex();

        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        EndPrimitive();

        // right side
        f_vertex = v_vertex[1];
        f_color = v_color[1];

        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        f_normal = g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_vert);
        EmitVertex();

        f_normal = -g_vertex_normal_horz_head;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz_head);
        EmitVertex();

        f_normal = -g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz);
        EmitVertex();

        EndPrimitive();

        f_normal = -g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz);
        EmitVertex();

        f_normal = -g_vertex_normal_vert;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_vert);
        EmitVertex();

        f_normal = -g_vertex_normal_horz_head;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz_head);
        EmitVertex();

        f_normal = g_vertex_normal_horz;
        gl_Position = u_viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz);
        EmitVertex();

        EndPrimitive();
    }

fragment =
    varying lowp vec4 f_color;
    //varying lowp vec4 f_material_color;
    varying lowp vec3 f_normal;
    varying lowp vec3 f_vertex;
    //flat varying lowp uint f_extruder;

    uniform mediump vec4 u_ambientColor;
    uniform highp vec3 u_lightPosition;

    void main()
    {
        mediump vec4 finalColor = vec4(0.0);
        float alpha = f_color.a;

        finalColor.rgb += f_color.rgb * 0.3;

        highp vec3 normal = normalize(f_normal);
        highp vec3 lightDir = normalize(u_lightPosition - f_vertex);

        // Diffuse Component
        highp float NdotL = clamp(dot(normal, lightDir), 0.0, 1.0);
        finalColor += (NdotL * f_color);
        finalColor.a = alpha;  // Do not change alpha in any way

        gl_FragColor = finalColor;
    }


[defaults]
u_active_extruder = 0.0
u_layer_view_type = 0
u_only_color_active_extruder = 1
u_extruder_opacity = [1.0, 1.0]

u_specularColor = [0.4, 0.4, 0.4, 1.0]
u_ambientColor = [0.3, 0.3, 0.3, 0.0]
u_diffuseColor = [1.0, 0.79, 0.14, 1.0]
u_shininess = 20.0

u_show_travel_moves = 0
u_show_support = 1
u_show_adhesion = 1
u_show_skin = 1
u_show_infill = 1

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
a_line_dim = line_dim
a_extruder = extruders
a_material_color = material_color
a_line_type = line_type
