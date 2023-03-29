#version 150

uniform sampler2D p3d_Texture0;
uniform mat3 p3d_NormalMatrix;
uniform mat4 p3d_ModelViewMatrix;

uniform vec4 colorPower;

// Input from vertex shader
in vec2 texcoord;
in vec3 normal;
in vec4 position;

// Output to the screen
out vec4 p3d_FragColor;

void main() {
    vec4 color = texture(p3d_Texture0, texcoord);
    vec3 normalCam = p3d_NormalMatrix * normal;
    vec4 positionCam = p3d_ModelViewMatrix * position;
    float val = abs(dot(normalCam, normalize(positionCam.xyz)));
    float multiplier = length(colorPower.rgb) / length(vec3(1.0f, 1.0f, 1.0f));
    if(multiplier < 0.1f) {
        float brightness = 1.0f - multiplier;
        color = vec4(brightness, brightness, brightness, 1.0f);
    }
    p3d_FragColor = color * colorPower * val;
}