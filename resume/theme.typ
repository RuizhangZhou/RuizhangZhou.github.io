#let section-title(title) = [
  #set text(weight: "bold", size: 11pt)
  #title
  #line(length: 100%, stroke: 0.6pt)
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
  #set text(size: 20pt, weight: "bold")
  #name \
  #set text(size: 10pt, weight: "regular")
  #subtitle \
  #show link: it => underline(text(fill: rgb("#0a66c2"), it))
  #contacts
]

#set page(margin: (
  top: 1.2cm,
  right: 1.4cm,
  bottom: 1.2cm,
  left: 1.4cm,
))
#set text(size: 10pt, leading: 1.15em)
#show link: it => underline(text(fill: rgb("#0a66c2"), it))
