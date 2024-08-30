/*
Define light sources to illuminate the atoms. For visualizing mediam
media_interaction and media_attenuation are set to "off" so voxel
data is rendered to be transparent. Lights are automatically oriented
with respect to the camera position.
*/

// Overhead light source
light_source {
    <0, 0, 10>
    color rgb <1,1,1>*0.5
    parallel
    point_at <ii, jj, kk>*0.5
    media_interaction off
    media_attenuation off
}

// Rear (forward-facing) light source
light_source {
    < (i-ii), (j-jj), (k-kk)>*4
    color rgb <1,1,1> * 0.5
    parallel
    point_at <ii, jj, kk>
    media_interaction off
    media_attenuation off
}

// Left light source
light_source {
    <( (i-ii)*cos(60*pi/180) - (j-jj)*sin(60*pi/180) ), ( (i-ii)*sin(60*pi/180) + (j-jj)*cos(60*pi/180) ), k>
    color rgb <1,1,1>*0.5
    parallel
    point_at <ii, jj, kk>
    media_interaction off
    media_attenuation off
}

// Right light source
light_source {
    <( (i-ii)*cos(-60*pi/180) - (j-jj)*sin(-60*pi/180) ), ( (i-ii)*sin(-60*pi/180) + (j-jj)*cos(-60*pi/180) ), k>
    color rgb <1,1,1>*0.5
    parallel
    point_at <ii, jj, kk>
    media_interaction off
    media_attenuation off
}