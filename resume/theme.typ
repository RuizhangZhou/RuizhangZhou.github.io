#let section-title(title) = [
  #set text(weight: "bold", size: 12pt)
  #title
  #set text(weight: "regular", size: 10pt)
]

#let item(text) = [
  - #text
]

#let header(name, subtitle, contacts) = [
  #set text(size: 20pt, weight: "bold")
  #name \
  #set text(size: 10pt, weight: "regular")
  #subtitle \
  #contacts
]

#set page(margin: 1.6cm)
#set text(size: 10pt)
