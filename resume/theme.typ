#let section-title(title) = [
  #set text(weight: "bold", size: 12pt)
  #title \
  #set text(weight: "regular", size: 10pt)
]

#let role(title, org, period) = [
  #set text(size: 10.5pt, weight: "bold")
  #title \
  #set text(size: 10pt, weight: "regular", fill: rgb("#555555"))
  #org • #period
]

#let item(text) = [
  - #text
]

#let header(name, subtitle, contacts) = [
  #show link: it => underline(text(fill: rgb("#0a66c2"), it))
  #grid(
    columns: (auto, 1fr),
    gutter: 1em,
    align: (left + horizon, right + horizon),
    row-gutter: 0pt,
    [#set text(size: 20pt, weight: "bold"); #name],
    [#set text(size: 9pt, weight: "regular"); #contacts]
  )
  #set text(size: 10pt, weight: "regular")
  #subtitle
]

<<<<<<< HEAD
#set page(margin: (top: 1cm, bottom: 1.6cm, left: 1.6cm, right: 1.6cm))
#set text(size: 10pt)
=======
#set page(margin: (
  top: 1.2cm,
  right: 1.4cm,
  bottom: 1.2cm,
  left: 1.4cm,
))
#set text(size: 10pt, leading: 1.15em)
>>>>>>> 739fbfb052f49d91839e4739f1baaa9eeb9c5344
#show link: it => underline(text(fill: rgb("#0a66c2"), it))
