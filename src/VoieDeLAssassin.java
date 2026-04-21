public class VoieDeLAssassin extends Voie {
    public VoieDeLAssassin() {
        super("Voie de l'assassin");
        competences.add(new Competence("Discretion", 1));
        competences.add(new Competence("Attaque sournoise", 2));
        competences.add(new Competence("Ombre mouvante", 3));
        competences.add(new Competence("Surprise", 4));
    }
}
