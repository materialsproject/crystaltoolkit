
size(300);
import solids;
// Camera information
currentprojection=orthographic (
camera=(8,5,4),
up=(0,0,1),
target=(0,0,0),
zoom=0.5
);

// Plot appearance parameters
real cylR=0.1;

// Basic function for drawing spheres
void drawSpheres(triple[] C, real R, pen p=currentpen){
  for(int i=0;i<C.length;++i){
    draw(sphere(C[i],R).surface(
                        new pen(int i, real j){return p;}
                        )
    );
  }
}

// Draw a cylinder
void Draw(guide3 g,pen p=currentpen){
  draw(
    cylinder(
      point(g,0),cylR,arclength(g),point(g,1)-point(g,0)
    ).surface(
               new pen(int i, real j){
                 return p;
               }
             )
  );
}



triple sphere1=(-0.8050000001609999, 0.46476696679060203, -0.6549999999999998);

triple sphere2=(0.8050000001609999, -0.46476696679060214, 1.9649999999999999);


triple[] spheres = {sphere1,sphere2};
drawSpheres(spheres, 0.5, rgb('3050f8'));

triple sphere1=(-0.8050000001609999, 0.46476696679060203, -2.62);

triple sphere2=(-0.8050000001609999, 0.46476696679060203, 2.62);

triple sphere3=(0.8050000001609999, -0.46476696679060214, 0.0);


triple[] spheres = {sphere1,sphere2,sphere3};
drawSpheres(spheres, 0.5, rgb('bfa6a6'));
pen connectPen=rgb('3050f8');

triple IPOS = (-0.8050000001609999, 0.46476696679060203, -0.6549999999999998);
triple FPOS = (-0.8050000001609999, 0.46476696679060203, -1.6375);
Draw(IPOS--FPOS, connectPen);

triple IPOS = (-0.8050000001609999, 0.46476696679060203, -0.6549999999999998);
triple FPOS = (0.0, -5.551115123125783e-17, -0.3274999999999999);
Draw(IPOS--FPOS, connectPen);

triple IPOS = (0.8050000001609999, -0.46476696679060214, 1.9649999999999999);
triple FPOS = (0.8050000001609999, -0.46476696679060214, 0.9824999999999999);
Draw(IPOS--FPOS, connectPen);

triple IPOS = (0.8050000001609999, -0.46476696679060214, 1.9649999999999999);
triple FPOS = (0.0, -5.551115123125783e-17, 2.2925);
Draw(IPOS--FPOS, connectPen);

pen connectPen=rgb('bfa6a6');

triple IPOS = (-0.8050000001609999, 0.46476696679060203, -2.62);
triple FPOS = (-0.8050000001609999, 0.46476696679060203, -1.6375);
Draw(IPOS--FPOS, connectPen);

triple IPOS = (-0.8050000001609999, 0.46476696679060203, 2.62);
triple FPOS = (0.0, -5.551115123125783e-17, 2.2925);
Draw(IPOS--FPOS, connectPen);

triple IPOS = (0.8050000001609999, -0.46476696679060214, 0.0);
triple FPOS = (0.8050000001609999, -0.46476696679060214, 0.9824999999999999);
Draw(IPOS--FPOS, connectPen);

triple IPOS = (0.8050000001609999, -0.46476696679060214, 0.0);
triple FPOS = (0.0, -5.551115123125783e-17, -0.3274999999999999);
Draw(IPOS--FPOS, connectPen);


triple IPOS = (-0.8050000000000005, -1.3943009000929465, -2.62);
triple FPOS = (2.4149999999999996, -1.3943009000929465, -2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-0.8050000000000005, -1.3943009000929465, -2.62);
triple FPOS = (-2.4149999999999996, 1.3943009000929465, -2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-0.8050000000000005, -1.3943009000929465, -2.62);
triple FPOS = (-0.8050000000000005, -1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (2.4149999999999996, -1.3943009000929465, -2.62);
triple FPOS = (0.8050000000000004, 1.3943009000929465, -2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (2.4149999999999996, -1.3943009000929465, -2.62);
triple FPOS = (2.4149999999999996, -1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-2.4149999999999996, 1.3943009000929465, -2.62);
triple FPOS = (0.8050000000000006, 1.3943009000929465, -2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-2.4149999999999996, 1.3943009000929465, -2.62);
triple FPOS = (-2.4149999999999996, 1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-0.8050000000000005, -1.3943009000929465, 2.62);
triple FPOS = (2.4149999999999996, -1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-0.8050000000000005, -1.3943009000929465, 2.62);
triple FPOS = (-2.4149999999999996, 1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (0.8050000000000004, 1.3943009000929465, -2.62);
triple FPOS = (0.8050000000000004, 1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (2.4149999999999996, -1.3943009000929465, 2.62);
triple FPOS = (0.8050000000000004, 1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);

triple IPOS = (-2.4149999999999996, 1.3943009000929465, 2.62);
triple FPOS = (0.8050000000000004, 1.3943009000929465, 2.62);
draw(IPOS--FPOS, dashed);
