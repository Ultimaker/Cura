[shaders]
vertex41core =
    #version 410
    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform lowp float u_active_extruder;
    uniform lowp float u_max_feedrate;
    uniform lowp float u_min_feedrate;
    uniform lowp float u_max_thickness;
    uniform lowp float u_min_thickness;
    uniform lowp float u_max_line_width;
    uniform lowp float u_min_line_width;
    uniform lowp float u_max_flow_rate;
    uniform lowp float u_min_flow_rate;
    uniform lowp int u_layer_view_type;
    uniform lowp mat4 u_extruder_opacity;  // currently only for max 16 extruders, others always visible

    uniform highp mat4 u_normalMatrix;

    in highp vec4 a_vertex;
    in lowp vec4 a_color;
    in lowp vec4 a_material_color;
    in highp vec4 a_normal;
    in highp vec2 a_line_dim;  // line width and thickness
    in highp float a_extruder;
    in highp float a_prev_line_type;
    in highp float a_line_type;
    in highp float a_vertex_index;
    in highp float a_feedrate;
    in highp float a_thickness;

    out lowp vec4 v_color;

    out highp vec3 v_vertex;
    out highp vec3 v_normal;
    out lowp vec2 v_line_dim;
    out highp int v_extruder;
    out highp mat4 v_extruder_opacity;
    out highp float v_prev_line_type;
    out highp float v_line_type;
    out highp float v_index;

    out lowp vec4 f_color;
    out highp vec3 f_vertex;
    out highp vec3 f_normal;

    vec4 feedrateGradientColor(float abs_value, float min_value, float max_value)
    {
        float value;
        if(abs(max_value - min_value) < 0.0001) //Max and min are equal (barring floating point rounding errors).
        {
            value = 0.5; //Pick a colour in exactly the middle of the range.
        }
        else
        {
            value = (abs_value - min_value) / (max_value - min_value);
        }
        float red = value;
        float green = 1-abs(1-4*value);
        if (value > 0.375)
        {
            green = 0.5;
        }
        float blue = max(1-4*value, 0);
        return vec4(red, green, blue, 1.0);
    }

    vec4 layerThicknessGradientColor(float abs_value, float min_value, float max_value)
    {
        float value;
        if(abs(max_value - min_value) < 0.0001) //Max and min are equal (barring floating point rounding errors).
        {
            value = 0.5; //Pick a colour in exactly the middle of the range.
        }
        else
        {
            value = (abs_value - min_value) / (max_value - min_value);
        }
        float red = min(max(4*value-2, 0), 1);
        float green = min(1.5*value, 0.75);
        if (value > 0.75)
        {
            green = value;
        }
        float blue = 0.75-abs(0.25-value);
        return vec4(red, green, blue, 1.0);
    }

    vec4 lineWidthGradientColor(float abs_value, float min_value, float max_value)
    {
        float value;
        if(abs(max_value - min_value) < 0.0001) //Max and min are equal (barring floating point rounding errors).
        {
            value = 0.5; //Pick a colour in exactly the middle of the range.
        }
        else
        {
            value = (abs_value - min_value) / (max_value - min_value);
        }
        float red = value;
        float green = 1 - abs(1 - 4 * value);
        if(value > 0.375)
        {
            green = 0.5;
        }
        float blue = max(1 - 4 * value, 0);
        return vec4(red, green, blue, 1.0);
    }

    float clamp(float v)
    {
        float t = v < 0 ? 0 : v;
        return t > 1.0 ? 1.0 : t;
    }

    // Inspired by https://stackoverflow.com/a/46628410
    vec4 flowRateGradientColor(float abs_value, float min_value, float max_value)
    {
        float t;
        if(abs(min_value - max_value) < 0.0001)
        {
          t = 0;
        }
        else
        {
          t = 2.0 * ((abs_value - min_value) / (max_value - min_value)) - 1;
        }
        float red = clamp(1.5 - abs(2.0 * t - 1.0));
        float green = clamp(1.5 - abs(2.0 * t));
        float blue = clamp(1.5 - abs(2.0 * t + 1.0));
        return vec4(red, green, blue, 1.0);
    }

    void main()
    {
        vec4 v1_vertex = a_vertex;
        v1_vertex.y -= a_line_dim.y / 2;  // half layer down

        vec4 world_space_vert = u_modelMatrix * v1_vertex;
        gl_Position = world_space_vert;
        // shade the color depending on the extruder index stored in the alpha component of the color

        switch (u_layer_view_type) {
            case 0:  // "Material color"
                v_color = a_material_color;
                break;
            case 1:  // "Line type"
                v_color = a_color;
                break;
            case 2:  // "Speed", or technically 'Feedrate'
                v_color = feedrateGradientColor(a_feedrate, u_min_feedrate, u_max_feedrate);
                break;
            case 3:  // "Layer thickness"
                v_color = layerThicknessGradientColor(a_line_dim.y, u_min_thickness, u_max_thickness);
                break;
            case 4:  // "Line width"
                v_color = lineWidthGradientColor(a_line_dim.x, u_min_line_width, u_max_line_width);
                break;
            case 5:  // "Flow"
                float flow_rate =  a_line_dim.x * a_line_dim.y * a_feedrate;
                v_color = flowRateGradientColor(flow_rate, u_min_flow_rate, u_max_flow_rate);
                break;
        }

        v_vertex = world_space_vert.xyz;
        v_normal = (u_normalMatrix * normalize(a_normal)).xyz;
        v_line_dim = a_line_dim;
        v_extruder = int(a_extruder);
        v_prev_line_type = a_prev_line_type;
        v_line_type = a_line_type;
        v_index = a_vertex_index;
        v_extruder_opacity = u_extruder_opacity;

        // for testing without geometry shader
        f_color = v_color;
        f_vertex = v_vertex;
        f_normal = v_normal;
    }

geometry41core =
    #version 410

    uniform highp mat4 u_modelMatrix;
    uniform highp mat4 u_viewMatrix;
    uniform highp mat4 u_projectionMatrix;

    uniform lowp vec4 u_starts_color;

    uniform int u_show_travel_moves;
    uniform int u_show_helpers;
    uniform int u_show_skin;
    uniform int u_show_infill;
    uniform int u_show_starts;

    uniform highp vec2 u_drawRange;

    layout(lines) in;
    layout(triangle_strip, max_vertices = 40) out;

    in vec4 v_color[];
    in vec3 v_vertex[];
    in vec3 v_normal[];
    in lowp vec2 v_line_dim[];
    in int v_extruder[];
    in mat4 v_extruder_opacity[];
    in float v_prev_line_type[];
    in float v_line_type[];
    in float v_index[];

    out vec4 f_color;
    out vec3 f_normal;
    out vec3 f_vertex;

    // Set the set of variables and EmitVertex
    void myEmitVertex(vec3 vertex, vec4 color, vec3 normal, vec4 pos) {
        f_vertex = vertex;
        f_color = color;
        f_normal = normal;
        gl_Position = pos;
        EmitVertex();
    }

    void main()
    {
        highp mat4 viewProjectionMatrix = u_projectionMatrix * u_viewMatrix;

        vec4 g_vertex_delta;
        vec3 g_vertex_normal_horz;  // horizontal and vertical in respect to layers
        vec4 g_vertex_offset_horz;  // vec4 to match gl_in[x].gl_Position
        vec3 g_vertex_normal_vert;
        vec4 g_vertex_offset_vert;
        vec3 g_vertex_normal_horz_head;
        vec4 g_vertex_offset_horz_head;

        float size_x;
        float size_y;

        if (u_drawRange[0] >= 0.0 && u_drawRange[1] >= 0.0 && (v_index[0] < u_drawRange[0] || v_index[0] >= u_drawRange[1]))
        {
             return;
        }
        if ((v_extruder_opacity[0][int(mod(v_extruder[0], 4))][v_extruder[0] / 4] == 0.0) && (v_line_type[0] != 8) && (v_line_type[0] != 9)) {
            return;
        }
        // See LayerPolygon; 8 is MoveCombingType, 9 is RetractionType
        if ((u_show_travel_moves == 0) && ((v_line_type[0] == 8) || (v_line_type[0] == 9))) {
            return;
        }
        if ((u_show_helpers == 0) && ((v_line_type[0] == 4) || (v_line_type[0] == 5) || (v_line_type[0] == 7) || (v_line_type[0] == 10) || v_line_type[0] == 11)) {
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
            size_x = 0.05;
        } else {
            size_x = v_line_dim[1].x / 2 + 0.01;  // radius, and make it nicely overlapping
        }
        size_y = v_line_dim[1].y / 2 + 0.01;

        g_vertex_delta = gl_in[1].gl_Position - gl_in[0].gl_Position; //Actual movement exhibited by the line.
        g_vertex_normal_horz_head = normalize(vec3(-g_vertex_delta.x, -g_vertex_delta.y, -g_vertex_delta.z)); //Lengthwise normal vector pointing backwards.
        g_vertex_offset_horz_head = vec4(g_vertex_normal_horz_head * size_x, 0.0); //Lengthwise offset vector pointing backwards.

        g_vertex_normal_horz = normalize(vec3(g_vertex_delta.z, g_vertex_delta.y, -g_vertex_delta.x)); //Normal vector pointing right.
        g_vertex_offset_horz = vec4(g_vertex_normal_horz * size_x, 0.0); //Offset vector pointing right.

        g_vertex_normal_vert = vec3(0.0, 1.0, 0.0); //Upwards normal vector.
        g_vertex_offset_vert = vec4(g_vertex_normal_vert * size_y, 0.0); //Upwards offset vector. Goes up by half the layer thickness.

        if ((v_line_type[0] == 8) || (v_line_type[0] == 9)) { //Travel or retraction moves.
            vec4 va_head = viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz_head + g_vertex_offset_vert);
            vec4 va_up =  viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz + g_vertex_offset_vert);
            vec4 va_down = viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_horz + g_vertex_offset_vert);
            vec4 vb_head =  viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz_head + g_vertex_offset_vert);
            vec4 vb_down = viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz + g_vertex_offset_vert);
            vec4 vb_up = viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz + g_vertex_offset_vert);

            // Travels: flat plane with pointy ends
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_up);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_head);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_down);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_up);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_down);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_up);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_head);
            //And reverse so that the line is also visible from the back side.
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_up);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_down);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_up);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_down);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_head);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_up);

            EndPrimitive();
        } else {
            vec4 va_m_horz = viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_horz); //Line start, left vertex.
            vec4 vb_m_horz = viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz); //Line end, left vertex.
            vec4 va_p_vert = viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_vert); //Line start, top vertex.
            vec4 vb_p_vert = viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_vert); //Line end, top vertex.
            vec4 va_p_horz = viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz); //Line start, right vertex.
            vec4 vb_p_horz = viewProjectionMatrix * (gl_in[1].gl_Position + g_vertex_offset_horz); //Line end, right vertex.
            vec4 va_m_vert = viewProjectionMatrix * (gl_in[0].gl_Position - g_vertex_offset_vert); //Line start, bottom vertex.
            vec4 vb_m_vert = viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_vert); //Line end, bottom vertex.
            vec4 va_head   = viewProjectionMatrix * (gl_in[0].gl_Position + g_vertex_offset_horz_head); //Line start, tip.
            vec4 vb_head   = viewProjectionMatrix * (gl_in[1].gl_Position - g_vertex_offset_horz_head); //Line end, tip.

            // All normal lines are rendered as 3d tubes.
            myEmitVertex(v_vertex[0], v_color[1], -g_vertex_normal_horz, va_m_horz);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_horz, vb_m_horz);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_p_vert);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_p_vert);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_horz, va_p_horz);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_horz, vb_p_horz);
            myEmitVertex(v_vertex[0], v_color[1], -g_vertex_normal_vert, va_m_vert);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_vert, vb_m_vert);
            myEmitVertex(v_vertex[0], v_color[1], -g_vertex_normal_horz, va_m_horz);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_horz, vb_m_horz);

            EndPrimitive();

            // left side
            myEmitVertex(v_vertex[0], v_color[1], -g_vertex_normal_horz, va_m_horz);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_vert, va_p_vert);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_horz_head, va_head);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_horz, va_p_horz);

            EndPrimitive();

            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_horz, va_p_horz);
            myEmitVertex(v_vertex[0], v_color[1], -g_vertex_normal_vert, va_m_vert);
            myEmitVertex(v_vertex[0], v_color[1], g_vertex_normal_horz_head, va_head);
            myEmitVertex(v_vertex[0], v_color[1], -g_vertex_normal_horz, va_m_horz);

            EndPrimitive();

            // right side
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_horz, vb_p_horz);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_vert, vb_p_vert);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_horz_head, vb_head);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_horz, vb_m_horz);

            EndPrimitive();

            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_horz, vb_m_horz);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_vert, vb_m_vert);
            myEmitVertex(v_vertex[1], v_color[1], -g_vertex_normal_horz_head, vb_head);
            myEmitVertex(v_vertex[1], v_color[1], g_vertex_normal_horz, vb_p_horz);

            EndPrimitive();
        }

        if ((u_show_starts == 1) && (v_prev_line_type[0] != 1) && (v_line_type[0] == 1)) {
            float w = size_x;
            float h = size_y;

            myEmitVertex(v_vertex[0] + vec3( w,  h,  w), u_starts_color, normalize(vec3( 1.0,  1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w,  h,  w, 0.0))); // Front-top-left
            myEmitVertex(v_vertex[0] + vec3(-w,  h,  w), u_starts_color, normalize(vec3(-1.0,  1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w,  h,  w, 0.0))); // Front-top-right
            myEmitVertex(v_vertex[0] + vec3( w, -h,  w), u_starts_color, normalize(vec3( 1.0, -1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w, -h,  w, 0.0))); // Front-bottom-left
            myEmitVertex(v_vertex[0] + vec3(-w, -h,  w), u_starts_color, normalize(vec3(-1.0, -1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w, -h,  w, 0.0))); // Front-bottom-right
            myEmitVertex(v_vertex[0] + vec3(-w, -h, -w), u_starts_color, normalize(vec3(-1.0, -1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w, -h, -w, 0.0))); // Back-bottom-right
            myEmitVertex(v_vertex[0] + vec3(-w,  h,  w), u_starts_color, normalize(vec3(-1.0,  1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w,  h,  w, 0.0))); // Front-top-right
            myEmitVertex(v_vertex[0] + vec3(-w,  h, -w), u_starts_color, normalize(vec3(-1.0,  1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w,  h, -w, 0.0))); // Back-top-right
            myEmitVertex(v_vertex[0] + vec3( w,  h,  w), u_starts_color, normalize(vec3( 1.0,  1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w,  h,  w, 0.0))); // Front-top-left
            myEmitVertex(v_vertex[0] + vec3( w,  h, -w), u_starts_color, normalize(vec3( 1.0,  1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w,  h, -w, 0.0))); // Back-top-left
            myEmitVertex(v_vertex[0] + vec3( w, -h,  w), u_starts_color, normalize(vec3( 1.0, -1.0,  1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w, -h,  w, 0.0))); // Front-bottom-left
            myEmitVertex(v_vertex[0] + vec3( w, -h, -w), u_starts_color, normalize(vec3( 1.0, -1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w, -h, -w, 0.0))); // Back-bottom-left
            myEmitVertex(v_vertex[0] + vec3(-w, -h, -w), u_starts_color, normalize(vec3(-1.0, -1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w, -h, -w, 0.0))); // Back-bottom-right
            myEmitVertex(v_vertex[0] + vec3( w,  h, -w), u_starts_color, normalize(vec3( 1.0,  1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4( w,  h, -w, 0.0))); // Back-top-left
            myEmitVertex(v_vertex[0] + vec3(-w,  h, -w), u_starts_color, normalize(vec3(-1.0,  1.0, -1.0)), viewProjectionMatrix * (gl_in[0].gl_Position + vec4(-w,  h, -w, 0.0))); // Back-top-right

            EndPrimitive();
        }
    }

fragment41core =
    #version 410
    in lowp vec4 f_color;
    in lowp vec3 f_normal;
    in lowp vec3 f_vertex;

    out vec4 frag_color;

    uniform mediump vec4 u_ambientColor;
    uniform mediump vec4 u_minimumAlbedo;
    uniform highp vec3 u_lightPosition;

    void main()
    {
        mediump vec4 finalColor = vec4(0.0);
        float alpha = f_color.a;

        finalColor.rgb += f_color.rgb * 0.2 + u_minimumAlbedo.rgb;

        highp vec3 normal = normalize(f_normal);
        highp vec3 light_dir = normalize(u_lightPosition - f_vertex);

        // Diffuse Component
        highp float NdotL = clamp(dot(normal, light_dir), 0.0, 1.0);
        finalColor += (NdotL * f_color);
        finalColor.a = alpha;  // Do not change alpha in any way

        frag_color = finalColor;
    }


[defaults]
u_active_extruder = 0.0
u_layer_view_type = 0
u_extruder_opacity = [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]

u_specularColor = [0.4, 0.4, 0.4, 1.0]
u_ambientColor = [0.3, 0.3, 0.3, 0.0]
u_diffuseColor = [1.0, 0.79, 0.14, 1.0]
u_minimumAlbedo = [0.1, 0.1, 0.1, 1.0]
u_shininess = 20.0

u_starts_color = [1.0, 1.0, 1.0, 1.0]

u_show_travel_moves = 0
u_show_helpers = 1
u_show_skin = 1
u_show_infill = 1
u_show_starts = 1

u_min_feedrate = 0
u_max_feedrate = 1

u_min_thickness = 0
u_max_thickness = 1

u_drawRange = [-1.0, -1.0]

[bindings]
u_modelMatrix = model_matrix
u_viewMatrix = view_matrix
u_projectionMatrix = projection_matrix
u_normalMatrix = normal_matrix
u_lightPosition = light_0_position
u_drawRange = draw_range

[attributes]
a_vertex = vertex
a_color = color
a_normal = normal
a_line_dim = line_dim
a_extruder = extruder
a_material_color = material_color
a_prev_line_type = prev_line_type
a_line_type = line_type
a_feedrate = feedrate
a_thickness = thickness
a_vertex_index = vertex_index
