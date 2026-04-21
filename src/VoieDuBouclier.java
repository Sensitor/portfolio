public class VoieDuBouclier extends Voie {
    public VoieDuBouclier() {
        super("Voie du bouclier");
        competences.add(new Competence("Proteger un allie", 1));
        competences.add(new Competence("Absorber un coup", 2));
        competences.add(new Competence("Absorber un sort", 3));
        competences.add(new Competence("Armure lourde", 4));
    }
}
