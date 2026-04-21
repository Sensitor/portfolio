public class Competence {
    private String nom;
    private int rang;
    private int coutEnPoints;
    private String description;

    public Competence(String nom, int rang) {
        this(nom, rang, "");
    }

    public Competence(String nom, int rang, String description) {
        this.nom = nom;
        this.rang = rang;
        this.coutEnPoints = (rang <= 2) ? 1 : 2;
        this.description = description;
    }

    public String getNom() { return nom; }
    public int getRang() { return rang; }
    public int getCout() { return coutEnPoints; }
    public String getDescription() { return description; }
}
