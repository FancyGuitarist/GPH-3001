#let abstract(T) = {
  grid(columns: (1cm,1fr,1cm),[],[*Résumé:* #T],[])
}

#let front_page(titre:[Analyse musicale en python], cours:[GPH-3001]) = {
figure(image("ul_logo.svg", width: 40%,),)
{let space = v(weak: true,1fr)
let name = [Antoine Veillette]
let departement = [génie physique, physique et d'optique]
let foot = [Du département de #departement\
Faculté des sciences et de génie\
Université Laval\
#datetime.today().display()]
show: it => {align(center)[#it]}

line(length: 100%)
[*#titre*]
line(length: 100%)
  space
  name
  space
  [Dans le cadre du cours: \ ]
  cours
  space
  foot
 }
}