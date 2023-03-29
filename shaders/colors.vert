#version 150

// Uniform inputs
uniform mat4 p3d_ModelViewProjectionMatrix;

// Vertex inputs
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec3 p3d_Normal;

// Output to fragment shader
out vec2 texcoord;
out vec4 position;
out vec3 normal;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoord = p3d_MultiTexCoord0;
    normal = p3d_Normal;
    position = p3d_Vertex;
}