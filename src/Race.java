public abstract class Race {
    private String nom;

    public Race(String nom) {
        this.nom = nom;
    }

    public abstract void appliquerModificateurs(Personnage p);

    public String getNom() {
        return nom;
    }
}
